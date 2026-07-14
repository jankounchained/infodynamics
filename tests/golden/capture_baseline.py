"""
Golden-output baseline capture: runs infodynamics's current, unmodified
analysis pipeline over fixed, committed inputs and serializes the results.

This module is the single source of truth for both:
  - the one-time snapshot capture below (`python tests/golden/capture_baseline.py`)
  - the permanent comparison test (tests/test_golden_baseline.py), which imports
    the fixtures and compute_outputs() from here so both sides compute from
    identical inputs with identical logic.

Do NOT hand-edit tests/golden/baseline_arrays.npz or baseline_meta.json --
regenerate them by re-running this script.
"""
import hashlib
import json
import os

import numpy as np
import pytest

pytest.importorskip("sentence_transformers")
pytest.importorskip("tslearn")
pytest.importorskip("scipy")

from infodynamics import (
    FooteNovelty,
    InfoDynamics,
    MultiscaleInfoDynamics,
    Scalogram,
    SignalClusterer,
    WindowedRollingDistance,
    structure_descriptors,
)
from infodynamics.text.embedding import Encoder

# --- Text fixtures -----------------------------------------------------
# Inline, committed string constants (not the untracked root CSV/UDPipe
# files) following the TEXT/MULTISCALE_TEXT convention in
# tests/test_pipeline.py. Each fixture is 48 short declarative sentences
# spanning four sub-topics (12 sentences each) so that a genuine,
# non-degenerate self-similarity structure emerges, and so that
# MultiscaleInfoDynamics's full default scales (2,3,5,8,13,21) and radii
# (3,5,8,13,21) all survive filtering (radius 21 needs n_chunks >= 43).

FIXTURE_A = (
    "Cats chase mice through the garden. Dogs bark loudly at strangers. "
    "Birds build nests in the spring. Fish swim upstream to spawn. "
    "Bees pollinate flowers all summer. Ants carry crumbs back to the colony. "
    "Owls hunt quietly at night. Wolves howl beneath a full moon. "
    "Deer graze at the edge of the forest. Rabbits burrow beneath the hedgerow. "
    "Squirrels bury acorns for winter. Foxes prowl the fields at dusk. "
    "The sun rises earlier in June. Rain falls steadily on the roof. "
    "Wind rattles the old wooden shutters. Snow blankets the hills in December. "
    "Thunder rumbles across the valley. Lightning splits the darkened sky. "
    "Fog settles over the quiet harbor. Frost coats the morning grass. "
    "Hail pelts the tin roof loudly. Clouds drift slowly past the peak. "
    "A rainbow arcs after the storm. Humidity thickens the summer air. "
    "Oak trees shed their leaves in autumn. Moss grows thick on damp stones. "
    "Rivers carve deep canyons over centuries. Volcanoes reshape the coastline slowly. "
    "Glaciers retreat further each decade. Wildflowers bloom across the meadow. "
    "Ferns unfurl beneath the canopy. Mountains rise where plates collide. "
    "Deserts expand as rainfall declines. Coral reefs bleach in warmer water. "
    "Mangroves anchor the muddy shoreline. Bamboo grows fastest after rain. "
    "Stars burn brighter far from cities. Planets orbit the sun in ellipses. "
    "Comets streak briefly across the night. Meteors flash and vanish quickly. "
    "The moon waxes and wanes monthly. Tides rise and fall with gravity. "
    "Galaxies spiral outward from their core. Black holes bend light around them. "
    "Satellites circle the earth silently. Telescopes reveal distant, ancient light. "
    "Auroras shimmer near the poles. Eclipses darken the sky briefly."
)

FIXTURE_B = (
    "Computers process instructions at incredible speed. Software engineers write code every day. "
    "Databases store records for later retrieval. Networks route packets across continents. "
    "Servers respond to thousands of requests. Algorithms sort data efficiently. "
    "Compilers translate code into machine instructions. Operating systems manage hardware resources. "
    "Browsers render web pages quickly. Firewalls block suspicious network traffic. "
    "Encryption protects sensitive information. Processors execute billions of cycles per second. "
    "Rockets launch payloads into orbit. Astronauts train for years before flight. "
    "Satellites monitor weather from above. Probes travel years to reach distant planets. "
    "Rovers traverse the dusty Martian surface. Space stations orbit the earth continuously. "
    "Engineers design heat shields for reentry. Telescopes capture images of distant galaxies. "
    "Mission control tracks every spacecraft maneuver. Fuel tanks are jettisoned after launch. "
    "Solar panels power orbiting satellites. Capsules splash down in the ocean. "
    "Ancient civilizations built great pyramids. Explorers charted unknown coastlines by ship. "
    "Empires rose and fell over centuries. Scholars preserved knowledge in old libraries. "
    "Traders exchanged goods along silk routes. Armies marched across vast open plains. "
    "Kings ruled from towering stone castles. Scribes recorded events on ancient scrolls. "
    "Revolutions reshaped entire nations quickly. Treaties ended long and costly wars. "
    "Inventors changed daily life forever. Historians debate the causes of decline. "
    "Doctors diagnose illness through careful examination. Vaccines train the immune system early. "
    "Surgeons repair damaged tissue precisely. Cells divide to replace old tissue. "
    "Genes carry instructions for every trait. Antibiotics fight many bacterial infections. "
    "Nurses monitor patients around the clock. Researchers study disease at the molecular level. "
    "Hospitals treat emergencies at all hours. Bones heal slowly after a fracture. "
    "Nutrients fuel the body's daily functions. Therapies target tumors with precision."
)

FIXTURE_C = (
    "Chefs chop vegetables quickly for dinner. Bakers knead dough early each morning. "
    "Ovens bake bread at high heat. Spices season the simmering stew. "
    "Knives slice through ripe tomatoes. Pots simmer sauce over low flame. "
    "Bread rises slowly on the counter. Butter melts into the warm pan. "
    "Herbs garnish the finished plate. Salt balances the dish's sweetness. "
    "Grills sear meat over open flame. Kitchens fill with the smell of garlic. "
    "Trains depart the station every hour. Planes cross oceans in a few hours. "
    "Ships sail slowly past rocky coastlines. Travelers pack light for long journeys. "
    "Maps guide hikers through dense forest. Hotels welcome guests after midnight. "
    "Airports bustle with early morning crowds. Passports get stamped at every border. "
    "Backpackers camp beneath open starry skies. Buses wind through narrow mountain roads. "
    "Tourists photograph ancient city landmarks. Ferries cross the strait each evening. "
    "Runners train hard before the marathon. Swimmers practice laps every single morning. "
    "Cyclists race along winding coastal roads. Players pass the ball down the field. "
    "Coaches plan strategy before every match. Fans cheer loudly from crowded stands. "
    "Referees enforce the rules of the game. Athletes stretch carefully before competing. "
    "Teams celebrate victory on the field. Goalkeepers block shots at the last second. "
    "Sprinters explode from the starting blocks. Climbers scale steep granite cliffs slowly. "
    "Musicians tune their instruments before the show. Painters mix colors on a wooden palette. "
    "Dancers rehearse routines for hours daily. Singers warm up their voices carefully. "
    "Sculptors shape clay into new forms. Composers write melodies late at night. "
    "Actors memorize lines before opening night. Photographers frame each shot with care. "
    "Poets read verses at the small cafe. Guitarists strum chords beneath the streetlight. "
    "Orchestras perform symphonies in grand halls. Artists sketch scenes in quiet parks."
)

FIXTURES = {"a": FIXTURE_A, "b": FIXTURE_B, "c": FIXTURE_C}

# --- Numeric (encoder-independent) fixture ------------------------------
NUMERIC_SEED = 20260713
NUMERIC_ARRAY_SHAPE = (60, 16)

# Full default multiscale surface (mirrors MultiscaleInfoDynamics defaults),
# used both to build the numeric-half Scalogram/FooteNovelty and as the
# expected-length reference in the determinism/coverage self-check below.
_DEFAULT_SCALES = (2, 3, 5, 8, 13, 21)
_DEFAULT_RADII = (3, 5, 8, 13, 21)

_GOLDEN_DIR = os.path.dirname(os.path.abspath(__file__))
ARRAYS_PATH = os.path.join(_GOLDEN_DIR, "baseline_arrays.npz")
META_PATH = os.path.join(_GOLDEN_DIR, "baseline_meta.json")


def compute_outputs():
    """Run the current, unmodified analysis pipeline over the fixed inputs
    above and return (arrays, meta): a dict of ndarray outputs and a dict
    of scalar/dict outputs, covering all six target estimators.

    Returns
    -------
    arrays : dict[str, np.ndarray]
    meta : dict
    """
    arrays = {}
    meta = {"fixtures": {}}

    # Real, network-independent (locally cached) encoder -- shared across
    # fixtures and pipelines. Pinned to device="cpu" for determinism.
    encoder = Encoder("sentence-transformers/all-MiniLM-L6-v2", device="cpu")

    for name, text in FIXTURES.items():
        info = InfoDynamics(encoder=encoder, window_size=3).fit_transform(text)
        arrays[f"{name}_novelty"] = np.asarray(info["novelty"])
        arrays[f"{name}_transience"] = np.asarray(info["transience"])
        arrays[f"{name}_resonance"] = np.asarray(info["resonance"])

        multiscale = MultiscaleInfoDynamics(encoder=encoder)
        result = multiscale.fit_transform(text)
        arrays[f"multiscale_{name}_ssm"] = np.asarray(result["ssm"])
        arrays[f"multiscale_{name}_scalogram"] = np.asarray(result["scalogram"])
        arrays[f"multiscale_{name}_novelty"] = np.asarray(result["novelty"])

        meta["fixtures"][name] = {
            "descriptors": result["descriptors"],
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "n_chunks": len(multiscale.chunks_),
            "scales": list(multiscale.scales_),
            "radii": list(multiscale.radii_),
        }

    # --- Pure-numeric half (encoder-independent) ------------------------
    rng = np.random.default_rng(NUMERIC_SEED)
    X = rng.standard_normal(NUMERIC_ARRAY_SHAPE)

    wrd_signal = WindowedRollingDistance(measure="cosine", window_size=3).fit_transform(X)
    arrays["numeric_wrd_N_hat"] = np.asarray(wrd_signal["N_hat"])
    arrays["numeric_wrd_T_hat"] = np.asarray(wrd_signal["T_hat"])
    arrays["numeric_wrd_R_hat"] = np.asarray(wrd_signal["R_hat"])

    scalogram = Scalogram(scales=_DEFAULT_SCALES)
    arrays["numeric_scalogram_matrix"] = np.asarray(scalogram.fit_transform(X))

    foote = FooteNovelty(radii=_DEFAULT_RADII)
    arrays["numeric_foote_novelty"] = np.asarray(foote.fit_transform(X))
    arrays["numeric_foote_ssm"] = np.asarray(foote.ssm_)

    numeric_descriptors = structure_descriptors(X)

    # --- Clustering half (encoder-independent, continues the same rng) --
    series = [rng.standard_normal(40) for _ in range(5)]
    clusterer = SignalClusterer(n_clusters=2).fit(series)
    arrays["cluster_labels"] = np.asarray(clusterer.labels_)
    for label, barycenter in clusterer.barycenters_.items():
        arrays[f"cluster_barycenter_{label}"] = np.asarray(barycenter)

    meta["numeric"] = {
        "seed": NUMERIC_SEED,
        "shape": list(NUMERIC_ARRAY_SHAPE),
        "descriptors": numeric_descriptors,
        "scalogram_scales": list(scalogram.scales_),
        "foote_radii": list(foote.radii_),
    }
    meta["cluster"] = {
        "n_clusters": clusterer.n_clusters_,
        "label_keys": sorted(int(k) for k in clusterer.barycenters_.keys()),
    }
    meta["shapes"] = {key: list(np.asarray(value).shape) for key, value in arrays.items()}

    return arrays, meta


if __name__ == "__main__":
    # Determinism self-check: two independent runs must agree within
    # tolerance before we trust either as the checked-in snapshot. Guards
    # the future comparison test against flakiness from the encoder or
    # DBA barycenter computation.
    arrays_1, meta_1 = compute_outputs()
    arrays_2, meta_2 = compute_outputs()

    assert set(arrays_1.keys()) == set(arrays_2.keys()), "compute_outputs() key sets disagree across runs"
    for key, value in arrays_1.items():
        other = arrays_2[key]
        assert np.allclose(value, other, rtol=1e-5, atol=1e-8), (
            f"determinism self-check failed for {key!r}: repeated compute_outputs() runs disagree"
        )
        assert not np.isnan(value).any(), f"{key!r} contains NaN"
        assert not np.isinf(value).any(), f"{key!r} contains Inf"

    # Full-default-surface survival check: the fixtures must be long enough
    # that MultiscaleInfoDynamics's, Scalogram's, and FooteNovelty's default
    # scales/radii are NOT silently dropped by the n_chunks filter.
    default_scales = MultiscaleInfoDynamics().scales
    default_radii = MultiscaleInfoDynamics().radii
    for name in FIXTURES:
        fixture_meta = meta_1["fixtures"][name]
        assert len(fixture_meta["scales"]) == len(default_scales), (
            f"fixture {name!r} silently dropped multiscale scales: "
            f"{fixture_meta['scales']} vs default {list(default_scales)}"
        )
        assert len(fixture_meta["radii"]) == len(default_radii), (
            f"fixture {name!r} silently dropped multiscale radii: "
            f"{fixture_meta['radii']} vs default {list(default_radii)}"
        )
    assert meta_1["numeric"]["scalogram_scales"] == list(_DEFAULT_SCALES), (
        "numeric fixture silently dropped Scalogram scales"
    )
    assert meta_1["numeric"]["foote_radii"] == list(_DEFAULT_RADII), (
        "numeric fixture silently dropped FooteNovelty radii"
    )

    # Serialize the checked-in snapshot.
    np.savez(ARRAYS_PATH, **arrays_1)
    with open(META_PATH, "w") as f:
        json.dump(meta_1, f, indent=2, sort_keys=True)

    print(f"Wrote {ARRAYS_PATH} and {META_PATH} ({len(arrays_1)} arrays).")
