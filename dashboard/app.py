"""
Evidence-bench Streamlit app — a thin UI over bench_core.

Run:
    cd dashboard
    pip install streamlit pyyaml pandas numpy matplotlib
    # (re)build the cache first, with your embeddings:
    EMB_BACKEND=qwen python build_dashboard_artifacts.py
    streamlit run app.py

Purpose: turn multi-scale structure signals into concrete, quotable agent
failures paired with Radomil's better handling, then export them as rules the
agent can consume.
"""
import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

import bench_core as bc
from taxonomy import FAILURE_MODES

sys.path.insert(0, os.path.dirname(bc.HERE))  # repo root, for the infodynamics package
from infodynamics import viz

st.set_page_config(page_title="Evidence bench", layout="wide")


@st.cache_resource
def load_bench():
    return bc.Bench()

b = load_bench()
ss = st.session_state
ss.setdefault("candidate", None)     # dict for the selected candidate
ss.setdefault("contrast", None)      # chosen contrast dict

PAGES = ["Overview", "Author signature", "Document detail", "Pair comparison",
         "Evidence bench"]
page = st.sidebar.radio("View", PAGES)
st.sidebar.caption(f"cache: {b.config['n_docs']} docs · "
                   f"{b.config['backend']} emb · dim {b.config['emb_dim']}")


# --------------------------------------------------------------------------- #
def resampled_novelty_wall(author):
    rows, labels = [], []
    sub = b.corpus[b.corpus.author == author]
    for _, r in sub.iterrows():
        nov1 = b.curves(r.doc_id)["nov1"]
        rows.append(np.interp(np.linspace(0, 1, 120),
                              np.linspace(0, 1, len(nov1)), nov1))
        labels.append(r.file_name[:28])
    return np.array(rows) if rows else np.zeros((0, 120)), labels


def doc_panel_fig(doc_id):
    """Full SSM / scalogram / Foote-novelty panel for one cached document —
    same three plots as run_multiscale_demo.plot_document_panel(), built from
    the dashboard cache instead of a freshly-fitted model."""
    file_name = b.corpus.loc[b.corpus.doc_id == doc_id, "file_name"].iloc[0]
    S = b.ssm(doc_id)
    cur = b.curves(doc_id)

    fig, axes = plt.subplots(3, 1, figsize=(5.5, 8.5))
    viz.plot_ssm(S, ax=axes[0])
    axes[0].set_title(f"{file_name}  ·  {S.shape[0]} sentences\n"
                      "Self-similarity matrix", fontsize=9)
    viz.plot_scalogram(cur["scalogram"], cur["scales"], ax=axes[1])
    axes[1].set_title("Scalogram (z-normalized rows)", fontsize=9)
    viz.plot_multiscale_novelty(cur["novelty"], cur["radii"], ax=axes[2])
    axes[2].set_title("Foote novelty", fontsize=9)
    fig.tight_layout()
    return fig


# ---- Overview -------------------------------------------------------------- #
if page == "Overview":
    st.title("Corpus overview")
    c1, c2 = st.columns([1.1, 1])

    with c1:
        st.subheader("Document map (PCA on structure descriptors)")
        fig, ax = plt.subplots(figsize=(6, 5))
        for a, col in [("ai", "#d1495b"), ("human", "#2e86ab")]:
            s = b.corpus[b.corpus.author == a]
            ax.scatter(s.mds_x, s.mds_y, c=col, label=a, alpha=0.75, s=40)
        ax.legend(); ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
        st.pyplot(fig)

        st.subheader("Most discriminating descriptors (|Cohen's d|)")
        disc = pd.DataFrame(b.aggregates["discriminative"])
        st.dataframe(disc, use_container_width=True, hide_index=True)

    with c2:
        st.subheader("Novelty wall (length-normalised, per document)")
        for a in ["ai", "human"]:
            wall, labels = resampled_novelty_wall(a)
            if not len(wall):
                continue
            st.markdown(f"**{a}** — {len(wall)} docs")
            fig, ax = plt.subplots(figsize=(6, max(1.5, len(wall) * 0.11)))
            ax.imshow(wall, aspect="auto", cmap="magma",
                      extent=[0, 1, len(wall), 0])
            ax.set_yticks([]); ax.set_xlabel("normalised position")
            st.pyplot(fig)


# ---- Author signature ------------------------------------------------------ #
elif page == "Author signature":
    st.title("Author signatures")
    agg = b.aggregates
    c1, c2, c3 = st.columns(3)

    with c1:
        st.subheader("Mean novelty profile")
        fig, ax = plt.subplots(figsize=(5, 4))
        for a, col in [("ai", "#d1495b"), ("human", "#2e86ab")]:
            p = agg["ref_profile"].get(a)
            if not p:
                continue
            m, sd = np.array(p["mean"]), np.array(p["std"])
            x = np.linspace(0, 1, len(m))
            ax.plot(x, m, color=col, label=a)
            ax.fill_between(x, m - sd, m + sd, color=col, alpha=0.15)
        ax.legend(); ax.set_xlabel("normalised position"); ax.set_ylabel("novelty")
        st.pyplot(fig)

    with c2:
        st.subheader("Scale-energy signature")
        fig, ax = plt.subplots(figsize=(5, 4))
        for a, col in [("ai", "#d1495b"), ("human", "#2e86ab")]:
            se = agg["scale_energy"].get(a)
            if not se:
                continue
            ax.plot(se["scales"], se["mean"], "o-", color=col, label=a)
        ax.set_xlabel("window (sentences)"); ax.set_ylabel("mean energy")
        ax.legend(); st.pyplot(fig)

    with c3:
        st.subheader("Rhythm (novelty autocorrelation)")
        fig, ax = plt.subplots(figsize=(5, 4))
        for a, col in [("ai", "#d1495b"), ("human", "#2e86ab")]:
            ac = agg["autocorr"].get(a)
            if not ac:
                continue
            ax.plot(range(len(ac)), ac, color=col, label=a)
        ax.axhline(0, color="k", lw=0.5); ax.set_xlabel("lag (sentences)")
        ax.set_ylabel("autocorr"); ax.legend(); st.pyplot(fig)
    st.caption("A periodicity peak at a fixed lag = mechanical/templated rhythm.")


# ---- Document detail ------------------------------------------------------- #
elif page == "Document detail":
    st.title("Document detail")
    doc_ids = b.corpus.doc_id.unique()
    doc_names = b.corpus.drop_duplicates("doc_id").set_index("doc_id")["file_name"]
    doc = st.selectbox("Document", doc_ids, format_func=lambda d: doc_names[d])
    S = b.ssm(doc); cur = b.curves(doc); sents = b.sentences(doc)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Self-similarity matrix")
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.imshow(S, cmap="magma", vmin=0, vmax=np.quantile(S, 0.99))
        st.pyplot(fig)
    with c2:
        st.subheader("Scalogram")
        scal = cur["scalogram"]; scales = cur["scales"]
        z = (scal - scal.mean(1, keepdims=True)) / (scal.std(1, keepdims=True) + 1e-9)
        fig, ax = plt.subplots(figsize=(5, 2.4))
        ax.imshow(z, aspect="auto", cmap="viridis", origin="lower")
        ax.set_yticks(range(len(scales))); ax.set_yticklabels(scales)
        st.pyplot(fig)
        st.subheader("Foote novelty")
        fig, ax = plt.subplots(figsize=(5, 2.4))
        for k, r in enumerate(cur["radii"]):
            ax.plot(cur["novelty"][k], lw=1, label=f"r={r}")
        ax.legend(fontsize=6, ncol=5); st.pyplot(fig)

    st.subheader("Redundant pairs in this document")
    dp = b.pairs[b.pairs.doc_id == doc].sort_values("sim", ascending=False)
    if len(dp):
        st.dataframe(dp[["i", "j", "sim", "text_i", "text_j"]].head(30),
                     use_container_width=True, hide_index=True)
    else:
        st.info("No redundancy candidates above threshold.")


# ---- Pair comparison -------------------------------------------------------- #
elif page == "Pair comparison":
    st.title("Pair comparison")
    st.caption("Full SSM / scalogram / novelty panel for two documents, side by side.")

    def doc_picker(label, key, default_author):
        st.subheader(label)
        author = st.selectbox("Author", ["(all)", "ai", "human"],
                              index=["(all)", "ai", "human"].index(default_author),
                              key=f"{key}_author")
        pool = b.corpus if author == "(all)" else b.corpus[b.corpus.author == author]
        projects = ["(all)"] + sorted(pool.project.unique())
        project = st.selectbox("Project", projects, key=f"{key}_project")
        if project != "(all)":
            pool = pool[pool.project == project]
        doc_ids = pool.doc_id.unique()
        doc_names = pool.drop_duplicates("doc_id").set_index("doc_id")["file_name"]
        return st.selectbox("Document", doc_ids, format_func=lambda d: doc_names[d],
                            key=f"{key}_doc")

    sel_a, sel_b = st.columns(2)
    with sel_a:
        doc_a = doc_picker("Document A", "cmp_a", "ai")
    with sel_b:
        doc_b = doc_picker("Document B", "cmp_b", "human")

    st.divider()
    panel_a, panel_b = st.columns(2)
    with panel_a:
        st.pyplot(doc_panel_fig(doc_a))
    with panel_b:
        st.pyplot(doc_panel_fig(doc_b))


# ---- Evidence bench -------------------------------------------------------- #
elif page == "Evidence bench":
    st.title("Evidence bench")
    left, right = st.columns([1.25, 1])

    with left:
        feed_kind = st.radio("Candidate feed",
                             ["Redundancy", "Flatness", "Pattern-first"],
                             horizontal=True)
        author = st.selectbox("Author", ["ai", "human"], index=0)
        projects = ["(all)"] + sorted(b.corpus.project.unique())
        project = st.selectbox("Project", projects)
        proj = None if project == "(all)" else project

        if feed_kind == "Redundancy":
            min_sim = st.slider("min cosine sim", 0.0, 1.0, 0.5, 0.01)
            feed = b.feed_redundancy(author, proj, min_sim=min_sim, top=300)
            st.caption(f"{len(feed)} candidates")
            for idx, r in feed.head(60).iterrows():
                with st.expander(f"[{r.sim:.2f}] {r.doc_id}  {r.i}↔{r.j}"):
                    st.write(f"**i ({r.i}):** {r.text_i}")
                    st.write(f"**j ({r.j}):** {r.text_j}")
                    if st.button("Select", key=f"sel{idx}"):
                        ss.candidate = dict(kind="pair", doc_id=r.doc_id,
                                            author=author, i=int(r.i), j=int(r.j),
                                            text_i=r.text_i, text_j=r.text_j,
                                            sim=float(r.sim))
                        ss.contrast = None

        elif feed_kind == "Flatness":
            feed = b.feed_flatness(author, proj, top=200)
            st.caption(f"{len(feed)} flat regions")
            for idx, r in feed.head(60).iterrows():
                with st.expander(f"{r.doc_id}  {r.start}–{r.end} "
                                 f"({int(r.length)} sents, lr={r.mean_local_red})"):
                    st.write(b.context(r.doc_id, int(r.start), 0), "…",
                             b.context(r.doc_id, int(r.end), 0))
                    if st.button("Select", key=f"self{idx}"):
                        ss.candidate = dict(kind="region", doc_id=r.doc_id,
                                            author=author, i=int(r.start),
                                            j=int(r.end),
                                            text=b.context(r.doc_id, int(r.start), 2))
                        ss.contrast = None
        else:
            feat = st.selectbox("Feature", [d["feature"] for d in
                                            b.aggregates["discriminative"]])
            asc = st.checkbox("ascending (low end)")
            st.dataframe(b.feed_by_pattern(feat, author, 20, asc),
                         use_container_width=True, hide_index=True)
            st.caption("Open a listed doc in 'Document detail' to pick sentences.")

    with right:
        st.subheader("Selected candidate")
        cand = ss.candidate
        if not cand:
            st.info("Select a candidate from the feed.")
        else:
            if cand["kind"] == "pair":
                st.write(f"**Doc:** {cand['doc_id']}  ·  sim={cand['sim']:.2f}")
                st.write(f"**i ({cand['i']}):** {cand['text_i']}")
                st.write(f"**j ({cand['j']}):** {cand['text_j']}")
                idxs = [cand["i"], cand["j"]]
            else:
                st.write(f"**Doc:** {cand['doc_id']}  ·  region "
                         f"{cand['i']}–{cand['j']}")
                st.write(cand.get("text", ""))
                idxs = list(range(cand["i"], cand["j"] + 1))

            if st.button("Suggest Radomil contrast"):
                ss.contrast = None
                sugg = b.suggest_contrast(cand["doc_id"], idxs, k=5)
                ss._sugg = sugg
            for si, sg in enumerate(ss.get("_sugg", []) or []):
                cols = st.columns([4, 1])
                cols[0].write(f"[{sg['sim']:.2f} · lr={sg['local_red']}] "
                              f"{sg['text']}")
                if cols[1].button("use", key=f"ct{si}"):
                    ss.contrast = sg
            if ss.contrast:
                st.success(f"Contrast: {ss.contrast['text'][:80]}")

            st.divider()
            mode = st.selectbox("Failure mode", list(FAILURE_MODES),
                                format_func=lambda m: f"{m} — {FAILURE_MODES[m]}")
            diagnosis = st.text_area("Diagnosis (why it's weak)")
            intentional = st.checkbox("Intentional device (not a defect)")
            if st.button("✚ Keep as finding", type="primary"):
                src = {"doc_id": cand["doc_id"], "author": cand["author"],
                       "i": cand["i"], "j": cand["j"]}
                quote = ({"text_i": cand["text_i"], "text_j": cand["text_j"]}
                         if cand["kind"] == "pair" else {"text": cand.get("text")})
                f = bc.Finding(failure_mode=mode, source=src, quote=quote,
                               metric_context={"sim": cand.get("sim")},
                               diagnosis=diagnosis, contrast=ss.contrast,
                               intentional_ok=intentional)
                b.add_finding(f)
                st.success("Saved to findings.jsonl")

    st.divider()
    st.subheader("Coverage / saturation")
    cov = b.coverage()
    st.dataframe(cov, use_container_width=True, hide_index=True)

    with st.expander("Promote a rule from findings"):
        findings = b.load_findings()
        kept = [f for f in findings if f["status"] != "dismissed"]
        opts = {f"{f['id']} · {f['failure_mode']}": f["id"] for f in kept}
        chosen = st.multiselect("Supporting findings", list(opts))
        rname = st.text_input("Rule name")
        rmode = st.selectbox("Mode", list(FAILURE_MODES), key="rmode")
        rstmt = st.text_area("Statement (imperative do/don't)")
        rrat = st.text_area("Rationale")
        if st.button("Promote rule") and chosen and rname:
            rid = b.promote_rule(rname, rmode, rstmt, rrat,
                                 [opts[c] for c in chosen])
            st.success(f"Promoted {rid}")

    with st.expander("Export"):
        if st.button("Build exports"):
            b.export_system_prompt(f"{bc.HERE}/export_system_prompt.md")
            b.export_style_guide(f"{bc.HERE}/export_style_guide.md")
            st.success("Wrote export_system_prompt.md and export_style_guide.md")
            st.code(b.export_system_prompt(), language="markdown")
