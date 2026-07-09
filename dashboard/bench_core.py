"""
Evidence-bench core logic — all cache reads and the finding/rule/export loop,
with NO Streamlit dependency so it can be unit-tested headlessly. app.py is a
thin UI over this.

Data flow (answers "where does the loop get its data"):
  candidate feeds      <- precomputed cache tables (redundant_pairs, flat_regions)
  contrast suggestion  <- cache embeddings + human_index (nearest-neighbour)
  findings / rules     <- human-authored store (findings.jsonl, rules.yaml)
The cache is disposable/recomputable; the store is precious/hand-editable.
"""
from __future__ import annotations
import os, json, time, uuid
from dataclasses import dataclass, field, asdict
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache")
FINDINGS_PATH = os.path.join(HERE, "findings.jsonl")
RULES_PATH = os.path.join(HERE, "rules.yaml")


# --------------------------------------------------------------------------- #
# records
# --------------------------------------------------------------------------- #
@dataclass
class Finding:
    failure_mode: str
    source: dict                       # {doc_id, author, i, j?, start?, end?}
    quote: dict                        # {text_i, text_j?} or {text}
    metric_context: dict = field(default_factory=dict)
    diagnosis: str = ""
    contrast: dict | None = None       # {doc_id, idx, text, sim}
    status: str = "kept"               # candidate|kept|dismissed
    intentional_ok: bool = False
    rule_id: str | None = None
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: float = field(default_factory=time.time)


# --------------------------------------------------------------------------- #
class Bench:
    def __init__(self, cache=CACHE):
        self.cache = cache
        self.config = json.load(open(f"{cache}/config.json"))
        self.corpus = pd.read_csv(f"{cache}/corpus.csv")
        self.pairs = pd.DataFrame(json.load(open(f"{cache}/redundant_pairs.json")))
        self.flat = pd.DataFrame(json.load(open(f"{cache}/flat_regions.json")))
        self.aggregates = json.load(open(f"{cache}/aggregates.json"))
        self._human = np.load(f"{cache}/human_index.npy")
        self._human_meta = json.load(open(f"{cache}/human_index_meta.json"))
        self._emb_cache, self._sent_cache = {}, {}

    # ---- lazy per-doc loaders ------------------------------------------- #
    def emb(self, doc_id):
        if doc_id not in self._emb_cache:
            self._emb_cache[doc_id] = np.load(f"{self.cache}/emb/{doc_id}.npy")
        return self._emb_cache[doc_id]

    def sentences(self, doc_id):
        if doc_id not in self._sent_cache:
            self._sent_cache[doc_id] = json.load(
                open(f"{self.cache}/sentences/{doc_id}.json"))
        return self._sent_cache[doc_id]

    def ssm(self, doc_id):
        return np.load(f"{self.cache}/ssm/{doc_id}.npy")

    def curves(self, doc_id):
        return np.load(f"{self.cache}/curves/{doc_id}.npz")

    # ---- morphology signal (optional -- see build_dashboard_artifacts.py) - #
    def morphology_available(self):
        return self.config.get("morphology_feature_group") is not None

    def morph_ssm(self, doc_id):
        return np.load(f"{self.cache}/morph_ssm/{doc_id}.npy")

    def morph_curves(self, doc_id):
        return np.load(f"{self.cache}/morph_curves/{doc_id}.npz")

    def morph_features(self, doc_id):
        """Per-sentence raw morphological feature values (e.g. pos_prop_VERB
        per sentence), joined with sentence text -- for direct inspection in
        the app, not just the derived ssm/scalogram/novelty signals."""
        X = np.load(f"{self.cache}/morph_features/{doc_id}.npy")
        names = self.config["morphology_feature_names"]
        df = pd.DataFrame(X, columns=names)
        df.insert(0, "text", [s["text"] for s in self.sentences(doc_id)])
        df.insert(0, "idx", range(len(df)))
        return df

    def context(self, doc_id, idx, window=1):
        s = self.sentences(doc_id)
        a, b = max(0, idx-window), min(len(s), idx+window+1)
        return " ".join(x["text"] for x in s[a:b])

    # ---- candidate feeds (read cache tables) ---------------------------- #
    def feed_redundancy(self, author="ai", project=None, min_sim=0.0, top=200):
        df = self.pairs
        df = df[df.author == author] if author else df
        if project:
            ids = set(self.corpus[self.corpus.project == project].doc_id)
            df = df[df.doc_id.isin(ids)]
        df = df[df.sim >= min_sim].sort_values("sim", ascending=False)
        return df.head(top).reset_index(drop=True)

    def feed_flatness(self, author="ai", project=None, top=200):
        df = self.flat
        df = df[df.author == author] if author else df
        if project:
            ids = set(self.corpus[self.corpus.project == project].doc_id)
            df = df[df.doc_id.isin(ids)]
        return df.sort_values("length", ascending=False).head(top).reset_index(drop=True)

    def feed_by_pattern(self, feature, author="ai", top=15, ascending=False):
        """Pattern-first entry: AI docs most extreme on a discriminating feature."""
        df = self.corpus[self.corpus.author == author]
        return df.sort_values(feature, ascending=ascending).head(top)[
            ["doc_id", "file_name", "project", feature]].reset_index(drop=True)

    # ---- contrast suggestion (nearest human, low redundancy) ------------ #
    def suggest_contrast(self, doc_id, idxs, k=5, max_local_red=0.5):
        emb = self.emb(doc_id)
        q = emb[list(idxs)].mean(0)
        q = q / (np.linalg.norm(q) + 1e-12)
        sims = self._human @ q
        order = np.argsort(-sims)
        out = []
        for r in order:
            m = self._human_meta[r]
            if m["local_red"] > max_local_red:
                continue
            out.append({**m, "sim": round(float(sims[r]), 4)})
            if len(out) >= k:
                break
        return out

    # ---- findings store -------------------------------------------------- #
    def load_findings(self):
        if not os.path.exists(FINDINGS_PATH):
            return []
        return [json.loads(l) for l in open(FINDINGS_PATH) if l.strip()]

    def add_finding(self, f: Finding):
        with open(FINDINGS_PATH, "a") as fh:
            fh.write(json.dumps(asdict(f), ensure_ascii=False) + "\n")
        return f.id

    def _rewrite(self, items):
        with open(FINDINGS_PATH, "w") as fh:
            for it in items:
                fh.write(json.dumps(it, ensure_ascii=False) + "\n")

    def update_finding(self, fid, **changes):
        items = self.load_findings()
        for it in items:
            if it["id"] == fid:
                it.update(changes)
        self._rewrite(items)

    def coverage(self):
        items = [f for f in self.load_findings() if f["status"] != "dismissed"]
        if not items:
            return pd.DataFrame(columns=["failure_mode", "n", "n_docs"])
        df = pd.DataFrame(items)
        g = df.groupby("failure_mode").agg(
            n=("id", "count"),
            n_docs=("source", lambda s: len({x["doc_id"] for x in s}))).reset_index()
        return g.sort_values("n", ascending=False)

    # ---- rules store ----------------------------------------------------- #
    def load_rules(self):
        import yaml
        if not os.path.exists(RULES_PATH):
            return []
        return yaml.safe_load(open(RULES_PATH)) or []

    def promote_rule(self, name, failure_mode, statement, rationale,
                     finding_ids, exemplar_ids=None, scope="all"):
        import yaml
        rules = self.load_rules()
        rid = "rule-" + uuid.uuid4().hex[:8]
        rules.append(dict(id=rid, name=name, failure_mode=failure_mode,
                          statement=statement, rationale=rationale,
                          supporting_findings=finding_ids,
                          exemplars=exemplar_ids or finding_ids[:2], scope=scope))
        yaml.safe_dump(rules, open(RULES_PATH, "w"), allow_unicode=True,
                       sort_keys=False)
        for fid in finding_ids:
            self.update_finding(fid, rule_id=rid)
        return rid

    # ---- exports --------------------------------------------------------- #
    def _finding_by_id(self, fid):
        for f in self.load_findings():
            if f["id"] == fid:
                return f
        return None

    def export_system_prompt(self, path=None):
        rules = self.load_rules()
        lines = ["# Writing rules for the Czech copy agent",
                 "# (auto-generated from the evidence bench)\n"]
        for r in rules:
            lines.append(f"## {r['name']}")
            lines.append(r["statement"])
            for fid in r.get("exemplars", []):
                f = self._finding_by_id(fid)
                if not f:
                    continue
                weak = f["quote"].get("text_i") or f["quote"].get("text")
                lines.append(f"- Weak (agent): „{weak}“")
                if f.get("contrast"):
                    lines.append(f"- Strong (Radomil): „{f['contrast']['text']}“")
            lines.append("")
        out = "\n".join(lines)
        if path:
            open(path, "w").write(out)
        return out

    def export_style_guide(self, path=None):
        rules = self.load_rules()
        by_mode = {}
        for r in rules:
            by_mode.setdefault(r["failure_mode"], []).append(r)
        lines = ["# Style guide — agent vs. Radomil\n"]
        for mode, rs in by_mode.items():
            lines.append(f"## {mode}")
            for r in rs:
                lines.append(f"### {r['name']}\n{r['statement']}\n\n{r['rationale']}\n")
        out = "\n".join(lines)
        if path:
            open(path, "w").write(out)
        return out


if __name__ == "__main__":
    b = Bench()
    print("docs", len(b.corpus), "redundancy candidates", len(b.pairs))
    print(b.feed_redundancy().head(3)[["doc_id", "sim"]].to_dict("records"))
