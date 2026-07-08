"""
Dedicated precompute for the evidence-bench dashboard.

Reads the corpus CSV, computes every artifact the Streamlit app needs, and
writes a self-contained cache. The app never recomputes anything expensive —
it only reads this cache (+ the human-authored findings store).

EMBEDDINGS ARE THE ONLY SWAP POINT.  Set BACKEND = "qwen" and everything else
is unchanged. TF-IDF fallback exists so the whole pipeline is runnable without
torch/network (e.g. in a sandbox); it uses a corpus-shared vocabulary so
cross-document nearest-neighbour (contrast search) is meaningful.

Run:  python build_dashboard_artifacts.py
Cache: dashboard/cache/
"""
from __future__ import annotations
import os, re, json, sys
from collections import Counter
import numpy as np
import pandas as pd

# import the multi-scale math (single source of truth)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scalogram_foote_prototype import (
    split_sentences, ssm, scalogram, multiscale_novelty, rolling_gap_distance,
)

# --------------------------------------------------------------------------- #
CONFIG = {
    "csv": "260708_radomil_collection.csv",
    "backend": os.environ.get("EMB_BACKEND", "tfidf"),   # "qwen" | "tfidf"
    "encoder_model": "Qwen/Qwen3-Embedding-8B",
    "authors": ["ai", "human"],          # 'draft' dropped from analysis
    "scales": [2, 3, 5, 8, 13, 21],
    "radii": [3, 5, 8, 13, 21],
    "ref_radius": 8,                     # radius used for 1-D novelty summaries
    "pair_min_gap": 5,                   # |i-j| must exceed this (skip near-diag)
    "pair_sim_thresh": 0.35,             # min cosine sim for a redundancy candidate
    "pair_top_k": 40,                    # cap candidates per doc
    "flat_min_len": 6,                   # min sentences for a flat region
    "flat_quantile": 0.30,               # novelty below this per-doc quantile = flat
    # tfidf fallback params
    "tfidf_min_df": 5, "tfidf_max_features": 8000,
}
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")


def slug(name: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "doc"


# --------------------------------------------------------------------------- #
# corpus-shared embeddings
# --------------------------------------------------------------------------- #
def _tok(s):
    return re.findall(r"[0-9a-zá-žčďěňřšťůúýžA-ZÁ-Ž]+", s.lower())

def _feats(s):
    toks = _tok(s)
    feats = list(toks)                                   # unigrams
    feats += [f"{a}_{b}" for a, b in zip(toks, toks[1:])]  # bigrams
    joined = " ".join(toks)
    feats += [joined[i:i+4] for i in range(len(joined)-3)]  # char 4-grams
    return feats

def embed_corpus_tfidf(all_sentences):
    """Shared-vocabulary TF-IDF; returns L2-normalized (N, V) float32."""
    df = Counter()
    per = []
    for s in all_sentences:
        f = _feats(s); per.append(f); df.update(set(f))
    keep = [f for f, c in df.items() if c >= CONFIG["tfidf_min_df"]]
    keep.sort(key=lambda f: -df[f])
    keep = keep[:CONFIG["tfidf_max_features"]]
    vocab = {f: i for i, f in enumerate(keep)}
    n, V = len(all_sentences), len(vocab)
    X = np.zeros((n, V), dtype=np.float32)
    for r, f in enumerate(per):
        for feat, c in Counter(f).items():
            j = vocab.get(feat)
            if j is not None:
                X[r, j] = c
    idf = np.log((1+n) / (1+np.array([df[f] for f in keep]))) + 1.0
    X *= idf
    nrm = np.linalg.norm(X, axis=1, keepdims=True); nrm[nrm == 0] = 1
    return X / nrm

def embed_corpus_qwen(all_sentences):
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer(CONFIG["encoder_model"])
    e = m.encode(all_sentences, normalize_embeddings=True,
                 convert_to_numpy=True, show_progress_bar=True)
    return np.asarray(e, dtype=np.float32)

def embed_corpus(all_sentences):
    return (embed_corpus_qwen if CONFIG["backend"] == "qwen"
            else embed_corpus_tfidf)(all_sentences)


# --------------------------------------------------------------------------- #
# per-doc analysis
# --------------------------------------------------------------------------- #
def local_redundancy(S, gap):
    """For each sentence, max similarity to any non-adjacent sentence."""
    n = S.shape[0]
    lr = np.zeros(n)
    for k in range(n):
        mask = np.abs(np.arange(n) - k) > gap
        lr[k] = float(S[k, mask].max()) if mask.any() else 0.0
    return lr

def ref_novelty(nov, radii):
    i = int(np.argmin([abs(r - CONFIG["ref_radius"]) for r in radii]))
    return nov[i]

def extract_pairs(doc_id, author, sents, S):
    n = S.shape[0]; g = CONFIG["pair_min_gap"]; th = CONFIG["pair_sim_thresh"]
    cand = []
    for i in range(n):
        for j in range(i + g + 1, n):
            s = float(S[i, j])
            if s >= th:
                cand.append((s, i, j))
    cand.sort(reverse=True)
    out = []
    for s, i, j in cand[:CONFIG["pair_top_k"]]:
        out.append(dict(doc_id=doc_id, author=author, i=i, j=j, sim=round(s, 4),
                        text_i=sents[i], text_j=sents[j]))
    return out

def extract_flat(doc_id, author, nov1, lr):
    th = np.quantile(nov1, CONFIG["flat_quantile"])
    regions, run = [], None
    for k, v in enumerate(nov1):
        if v <= th:
            run = (run[0], k) if run else (k, k)
        else:
            if run and run[1]-run[0]+1 >= CONFIG["flat_min_len"]:
                a, b = run
                regions.append(dict(doc_id=doc_id, author=author, start=a, end=b,
                                    length=b-a+1,
                                    mean_local_red=round(float(lr[a:b+1].mean()), 4)))
            run = None
    if run and run[1]-run[0]+1 >= CONFIG["flat_min_len"]:
        a, b = run
        regions.append(dict(doc_id=doc_id, author=author, start=a, end=b,
                            length=b-a+1,
                            mean_local_red=round(float(lr[a:b+1].mean()), 4)))
    return regions

def descriptors(emb, S, nov1, lr):
    off = S[np.triu_indices_from(S, k=1)]
    d5 = rolling_gap_distance(emb, 5)
    peaks = int(((nov1[1:-1] > nov1[:-2]) & (nov1[1:-1] > nov1[2:])).sum())
    return {
        "n_sentences": int(emb.shape[0]),
        "mean_offdiag_sim": float(off.mean()),
        "p90_offdiag_sim": float(np.quantile(off, 0.9)),
        "dist_var_w5": float(np.nanvar(d5)),
        "dist_mean_w5": float(np.nanmean(d5)),
        "novelty_var": float(np.var(nov1)),
        "mean_local_red": float(lr.mean()),
        "boundary_rate": float(peaks / max(1, emb.shape[0]) * 100),
    }


# --------------------------------------------------------------------------- #
# corpus-level aggregates
# --------------------------------------------------------------------------- #
def pca2(M):
    Z = (M - M.mean(0)) / (M.std(0) + 1e-9)
    U, S_, Vt = np.linalg.svd(Z, full_matrices=False)
    return (U[:, :2] * S_[:2])

def cohens_d(a, b):
    a, b = np.asarray(a), np.asarray(b)
    na, nb = len(a), len(b)
    sp = np.sqrt(((na-1)*a.var(ddof=1) + (nb-1)*b.var(ddof=1)) / max(1, na+nb-2))
    return float((a.mean() - b.mean()) / (sp + 1e-12))

def auc(a, b):
    a, b = np.asarray(a), np.asarray(b)
    allv = np.concatenate([a, b]); r = allv.argsort().argsort() + 1
    ra = r[:len(a)].sum()
    return float((ra - len(a)*(len(a)+1)/2) / (len(a)*len(b)))


# --------------------------------------------------------------------------- #
def main():
    os.makedirs(CACHE, exist_ok=True)
    for sub in ["sentences", "ssm", "curves", "emb"]:
        os.makedirs(os.path.join(CACHE, sub), exist_ok=True)

    csv = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       CONFIG["csv"])
    df = pd.read_csv(csv); df["content"] = df.content.fillna("")
    df = df[df.author.isin(CONFIG["authors"])].reset_index(drop=True)

    # segment every doc, keep a flat list of sentences for shared embedding
    docs, flat, owner = [], [], []
    for _, row in df.iterrows():
        sents = split_sentences(row.content)
        if len(sents) < 12:            # skip tiny docs
            continue
        did = slug(row.file_name)
        docs.append(dict(doc_id=did, file_name=row.file_name, author=row.author,
                         project=str(row.project), subproject=str(row.subproject),
                         sents=sents))
        for k, s in enumerate(sents):
            flat.append(s); owner.append((len(docs)-1, k))

    print(f"{len(docs)} docs, {len(flat)} sentences. Embedding ({CONFIG['backend']})...")
    E = embed_corpus(flat)

    # split embeddings back per doc
    for d in docs:
        d["emb"] = np.zeros((len(d["sents"]), E.shape[1]), dtype=np.float32)
    for (di, k), vec in zip(owner, E):
        docs[di]["emb"][k] = vec

    corpus_rows, all_pairs, all_flat = [], [], []
    ref_profiles = {}; scale_energy = {}; autocorr = {}
    human_vecs, human_meta = [], []

    for d in docs:
        did, emb, sents = d["doc_id"], d["emb"], d["sents"]
        S = ssm(emb)
        scal, scales = scalogram(emb, CONFIG["scales"])
        nov, radii = multiscale_novelty(S, CONFIG["radii"])
        nov1 = ref_novelty(nov, radii)
        lr = local_redundancy(S, CONFIG["pair_min_gap"])
        desc = descriptors(emb, S, nov1, lr)

        # persist per-doc arrays
        np.save(f"{CACHE}/ssm/{did}.npy", S.astype(np.float32))
        np.save(f"{CACHE}/emb/{did}.npy", emb)
        np.savez(f"{CACHE}/curves/{did}.npz", scalogram=scal.astype(np.float32),
                 novelty=nov.astype(np.float32), nov1=nov1.astype(np.float32),
                 local_red=lr.astype(np.float32),
                 scales=np.array(scales), radii=np.array(radii))
        with open(f"{CACHE}/sentences/{did}.json", "w") as f:
            json.dump([{"idx": i, "text": s} for i, s in enumerate(sents)],
                      f, ensure_ascii=False)

        all_pairs += extract_pairs(did, d["author"], sents, S)
        all_flat += extract_flat(did, d["author"], nov1, lr)
        corpus_rows.append({"doc_id": did, "file_name": d["file_name"],
                            "author": d["author"], "project": d["project"],
                            "subproject": d["subproject"], **desc})

        # aggregates inputs
        ref_profiles.setdefault(d["author"], []).append(
            np.interp(np.linspace(0, 1, 100), np.linspace(0, 1, len(nov1)), nov1))
        # align per-scale energy to the full CONFIG scale list (short docs drop scales)
        se = np.full(len(CONFIG["scales"]), np.nan)
        pos = {w: i for i, w in enumerate(CONFIG["scales"])}
        for wi, w in enumerate(scales):
            se[pos[w]] = scal[wi].var()
        scale_energy.setdefault(d["author"], []).append(se)
        ac = np.correlate(nov1-nov1.mean(), nov1-nov1.mean(), "full")
        ac = ac[ac.size//2:][:31]; ac = ac/ac[0] if ac[0] else ac
        autocorr.setdefault(d["author"], []).append(np.pad(ac, (0, 31-len(ac))))

        if d["author"] == "human":
            for k in range(len(sents)):
                human_vecs.append(emb[k])
                human_meta.append({"doc_id": did, "idx": k, "text": sents[k],
                                   "local_red": round(float(lr[k]), 4)})

    corpus = pd.DataFrame(corpus_rows)

    # doc map via PCA on descriptors
    feat_cols = ["mean_offdiag_sim", "p90_offdiag_sim", "dist_var_w5",
                 "novelty_var", "mean_local_red", "boundary_rate"]
    coords = pca2(corpus[feat_cols].to_numpy())
    corpus["mds_x"], corpus["mds_y"] = coords[:, 0], coords[:, 1]

    # discriminative ranking
    disc = []
    ai = corpus[corpus.author == "ai"]; hu = corpus[corpus.author == "human"]
    for c in feat_cols + ["dist_mean_w5", "n_sentences"]:
        disc.append({"feature": c, "cohens_d": round(cohens_d(ai[c], hu[c]), 3),
                     "auc": round(auc(ai[c], hu[c]), 3),
                     "ai_mean": round(float(ai[c].mean()), 4),
                     "human_mean": round(float(hu[c].mean()), 4)})
    disc.sort(key=lambda r: -abs(r["cohens_d"]))

    aggregates = {
        "ref_profile": {a: {"mean": np.mean(v, 0).tolist(),
                            "std": np.std(v, 0).tolist()}
                        for a, v in ref_profiles.items()},
        "scale_energy": {a: {"scales": CONFIG["scales"],
                             "mean": np.nanmean(v, 0).tolist()}
                         for a, v in scale_energy.items()},
        "autocorr": {a: np.mean(v, 0).tolist() for a, v in autocorr.items()},
        "discriminative": disc,
    }

    # write corpus-level artifacts
    corpus.to_csv(f"{CACHE}/corpus.csv", index=False)
    json.dump(all_pairs, open(f"{CACHE}/redundant_pairs.json", "w"),
              ensure_ascii=False)
    json.dump(all_flat, open(f"{CACHE}/flat_regions.json", "w"), ensure_ascii=False)
    json.dump(aggregates, open(f"{CACHE}/aggregates.json", "w"), ensure_ascii=False)
    np.save(f"{CACHE}/human_index.npy", np.array(human_vecs, dtype=np.float32))
    json.dump(human_meta, open(f"{CACHE}/human_index_meta.json", "w"),
              ensure_ascii=False)
    json.dump({**CONFIG, "n_docs": len(docs), "n_sentences": len(flat),
               "emb_dim": int(E.shape[1])},
              open(f"{CACHE}/config.json", "w"), ensure_ascii=False, indent=2)

    print(f"cache -> {CACHE}")
    print(f"  docs={len(docs)}  pairs={len(all_pairs)}  flat={len(all_flat)}  "
          f"human_sents={len(human_vecs)}")
    print("top discriminators:",
          [(d["feature"], d["cohens_d"]) for d in disc[:4]])


if __name__ == "__main__":
    main()
