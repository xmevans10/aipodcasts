"""Per-show discovery terms for story selection.

This is the *selection* vocabulary, separate from delivery (hosts.py). Each show
maps to a small set of search terms; a candidate is only a story if it matches at
least one show's beat. Dialogue shows list both presenters but share one beat.
"""
from __future__ import annotations

# host id -> search terms for discovery
BEATS: dict[str, list[str]] = {
    # solo shows
    "nova": ["moon", "solar system", "exoplanet", "cosmology"],
    "fern": ["animal behaviour", "wildlife", "bird", "mammal"],
    "ada": ["neuroscience", "brain", "cognition", "sensory processing"],
    "atlas": ["ocean", "climate", "glacier", "earth system"],
    "spinner": ["spider", "silk", "arachnid", "web"],
    "yusuf": ["star", "stellar", "astrochemistry", "spectroscopy"],
    "noor": ["machine learning", "neural network", "artificial intelligence", "language model"],
    "marek": ["3d printing", "additive manufacturing", "printed lattice", "polymer extrusion"],
    "tomas": ["biomechanics", "exercise", "muscle", "physical performance"],
    "lena": ["sleep", "circadian", "dreaming", "rest"],
    "rosa": ["fungus", "mycelium", "decomposition", "symbiosis"],
    "amara": ["bee", "pollination", "insect behaviour", "bee colony"],
    "kenji": ["deep sea", "hydrothermal vent", "abyssal", "deep ocean"],
    "freya": ["ancient dna", "archaeology", "migration", "genome"],
    # dialogue shows: one beat, keyed by the first presenter; dialogue_hosts expands
    "ines": ["replication", "statistical methods", "meta-analysis", "measurement error"],
    "jax": ["astrophysics", "black hole", "galaxy", "cosmic"],
}

# Presenter ids that belong to a dialogue show and should be reached through the
# first-listed member above (so the shortlist does not list a show twice).
DIALOGUE_MEMBERS = {"dev": "ines", "kai": "jax", "benny": "jax", "chase": "jax"}


def normalize_host(host_id: str) -> str:
    return DIALOGUE_MEMBERS.get(host_id, host_id)
