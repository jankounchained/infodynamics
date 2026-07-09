"""Controlled (but extensible) vocabulary of agent failure modes.

Predefined-but-extensible: the bench offers these first for clean aggregation,
but you can add ad-hoc tags and consolidate later. Keep slugs stable — findings
and rules reference them.
"""

FAILURE_MODES = {
    "redundancy-restatement": "Restates an earlier point with no new information.",
    "slogan-inflation": "Piles near-synonymous slogans/claims (padding, not content).",
    "structural-flatness": "Long stretch with no real topic development.",
    "filler-hedging": "Empty qualifiers, throat-clearing, hedges.",
    "register-mismatch": "Tone/register wrong for the audience.",
    # englishism lane (separate signal; slots reserved for v2)
    "englishism-collocation": "Unnatural Czech collocation / calque.",
    "englishism-word-order": "English-driven word order.",
    "englishism-literal": "Literal translation of an English idiom.",
    # positive / non-defect
    "intentional-device": "Repetition/parallelism used deliberately (NOT a defect).",
}

# which modes are "defects" to fix vs. captured as positive/neutral evidence
DEFECT_MODES = [m for m in FAILURE_MODES if m != "intentional-device"]
