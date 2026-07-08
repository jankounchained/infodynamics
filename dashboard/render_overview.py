"""Headless render of the corpus-level views (no Streamlit) for quick review."""
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import bench_core as bc

b = bc.Bench()
AI, HU = "#d1495b", "#2e86ab"

def wall(author):
    rows = []
    for _, r in b.corpus[b.corpus.author == author].iterrows():
        n = b.curves(r.doc_id)["nov1"]
        rows.append(np.interp(np.linspace(0, 1, 120), np.linspace(0, 1, len(n)), n))
    return np.array(rows)

fig = plt.figure(figsize=(15, 9))
gs = fig.add_gridspec(2, 3, hspace=0.35, wspace=0.3)

# doc map
ax = fig.add_subplot(gs[0, 0])
for a, c in [("ai", AI), ("human", HU)]:
    s = b.corpus[b.corpus.author == a]
    ax.scatter(s.mds_x, s.mds_y, c=c, label=a, alpha=0.75, s=40)
ax.legend(); ax.set_title("Document map (PCA on structure descriptors)")
ax.set_xlabel("PC1"); ax.set_ylabel("PC2")

# novelty walls
for i, a in enumerate(["ai", "human"]):
    ax = fig.add_subplot(gs[0, 1 + i])
    w = wall(a)
    ax.imshow(w, aspect="auto", cmap="magma", extent=[0, 1, len(w), 0])
    ax.set_title(f"Novelty wall — {a} ({len(w)} docs)")
    ax.set_xlabel("normalised position"); ax.set_yticks([])

agg = b.aggregates
# novelty profile
ax = fig.add_subplot(gs[1, 0])
for a, c in [("ai", AI), ("human", HU)]:
    p = agg["ref_profile"][a]; m, sd = np.array(p["mean"]), np.array(p["std"])
    x = np.linspace(0, 1, len(m)); ax.plot(x, m, color=c, label=a)
    ax.fill_between(x, m - sd, m + sd, color=c, alpha=0.15)
ax.set_title("Mean novelty profile"); ax.legend(); ax.set_xlabel("norm. position")

# scale energy
ax = fig.add_subplot(gs[1, 1])
for a, c in [("ai", AI), ("human", HU)]:
    se = agg["scale_energy"][a]; ax.plot(se["scales"], se["mean"], "o-", color=c, label=a)
ax.set_title("Scale-energy signature"); ax.set_xlabel("window (sent.)"); ax.legend()

# autocorr
ax = fig.add_subplot(gs[1, 2])
for a, c in [("ai", AI), ("human", HU)]:
    ac = agg["autocorr"][a]; ax.plot(range(len(ac)), ac, color=c, label=a)
ax.axhline(0, color="k", lw=0.5); ax.set_title("Rhythm (novelty autocorrelation)")
ax.set_xlabel("lag (sentences)"); ax.legend()

fig.suptitle(f"Evidence-bench corpus views — AI vs human ({b.config['model_name']} embeddings)",
             fontsize=14, y=0.98)
fig.savefig("corpus_overview.png", dpi=130, bbox_inches="tight")
print("saved corpus_overview.png")

# print top discriminators + a couple of concrete redundancy finds
print("\nTop discriminators (Cohen's d):")
for d in agg["discriminative"][:5]:
    print(f"  {d['feature']:>18}  d={d['cohens_d']:+.2f}  auc={d['auc']:.2f}  "
          f"ai={d['ai_mean']}  human={d['human_mean']}")
print("\nSharpest AI redundancy candidates (verbatim/near-verbatim repeats):")
top = b.feed_redundancy('ai', min_sim=0.9, top=6)
for _, r in top.iterrows():
    print(f"  [{r.sim:.2f}] {r.doc_id} {r.i}↔{r.j}: {r.text_i[:55]}")
