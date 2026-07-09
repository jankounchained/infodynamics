"""Headless end-to-end test of the evidence-bench loop (no Streamlit)."""
import os, json, tempfile
import bench_core as bc

# use throwaway store files in a temp dir so we never touch the real store/repo
_tmp = tempfile.mkdtemp(prefix="bench_test_")
bc.FINDINGS_PATH = os.path.join(_tmp, "findings.jsonl")
bc.RULES_PATH = os.path.join(_tmp, "rules.yaml")

b = bc.Bench()
print(f"[load] {len(b.corpus)} docs | {len(b.pairs)} redundancy | "
      f"{len(b.flat)} flat | human_index {b._human.shape}")

# 1. candidate feed
feed = b.feed_redundancy(author="ai", top=5)
assert len(feed) > 0, "redundancy feed empty"
c = feed.iloc[0]
print(f"[feed] top AI pair sim={c.sim} doc={c.doc_id} i={c.i} j={c.j}")
print(f"       text_i: {c.text_i[:70]}")
print(f"       text_j: {c.text_j[:70]}")

# 2. contrast suggestion (nearest low-redundancy human sentence)
sugg = b.suggest_contrast(c.doc_id, [c.i, c.j], k=3)
assert len(sugg) > 0, "no contrast suggestions"
print(f"[contrast] best human sim={sugg[0]['sim']} lr={sugg[0]['local_red']}")
print(f"           {sugg[0]['text'][:70]}")

# 3. create a Finding from the candidate + judgment
f = bc.Finding(
    failure_mode="redundancy-restatement",
    source={"doc_id": c.doc_id, "author": "ai", "i": int(c.i), "j": int(c.j)},
    quote={"text_i": c.text_i, "text_j": c.text_j},
    metric_context={"sim": float(c.sim)},
    diagnosis="Restates the same claim; no new information.",
    contrast=sugg[0],
)
fid = b.add_finding(f)
# a second finding to test coverage/saturation
c2 = feed.iloc[1]
b.add_finding(bc.Finding(
    failure_mode="redundancy-restatement",
    source={"doc_id": c2.doc_id, "author": "ai", "i": int(c2.i), "j": int(c2.j)},
    quote={"text_i": c2.text_i, "text_j": c2.text_j},
    metric_context={"sim": float(c2.sim)}))
print(f"[findings] stored {len(b.load_findings())} findings")

# 4. coverage view
cov = b.coverage()
print("[coverage]", cov.to_dict("records"))
assert cov.iloc[0]["n"] == 2

# 5. promote a rule and export
rid = b.promote_rule(
    name="One statement per point",
    failure_mode="redundancy-restatement",
    statement="State each point once. Do not re-summarise body points in list form.",
    rationale="The agent inflates length by restating; Radomil states once and moves on.",
    finding_ids=[fid])
print(f"[rule] promoted {rid}; rules now {len(b.load_rules())}")

sp = b.export_system_prompt(os.path.join(_tmp, "system_prompt.md"))
sg = b.export_style_guide(os.path.join(_tmp, "style_guide.md"))
assert "Weak (agent)" in sp and "One statement per point" in sp
print("[export] system_prompt_snippet + style_guide OK")
print("--- system prompt snippet ---")
print(sp)

# 6. pattern-first feed + flatness feed smoke test
pat = b.feed_by_pattern("mean_local_red", author="ai", top=3)
flat = b.feed_flatness(author="ai", top=3)
print(f"[pattern] top-3 by mean_local_red: {list(pat.doc_id)}")
print(f"[flat] {len(flat)} flat regions; longest={int(flat.iloc[0].length)} sents"
      if len(flat) else "[flat] none")

# cleanup throwaway store (temp dir, safe to remove)
import shutil
shutil.rmtree(_tmp, ignore_errors=True)
print("\nALL CHECKS PASSED")
