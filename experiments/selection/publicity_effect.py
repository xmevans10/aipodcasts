#!/usr/bin/env python3
"""Did the publicity signal move selection in the intended direction?

The existing sensitivity.py perturbs the shortlist's weighted-sum model. This one
measures the *autoselect* rank-aggregation after adding a collapsed publicity signal
(see docs/editorial/story-discovery.md). It is deterministic and offline: a synthetic
corpus of otherwise-identical papers isolates each signal, so the effect is the signal,
not the corpus.

It reports four things:
  1. Direction     a publicized paper outranks an otherwise-equal non-publicized one
  2. Priority      a press release (tier 1) edges out independent editorial (tier 2)
  3. Collapse      one release and three syndicated copies yield the same signal
  4. Robustness    top-K is stable when the publicity weight is halved or raised 50%

    python3 experiments/selection/publicity_effect.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from autoselect import SIGNAL_WEIGHTS, fuse  # noqa: E402
from publicity import Release, cluster_releases, publicity_value  # noqa: E402

HERE = Path(__file__).resolve().parent


def work(doi, *, publicity=0.0, editorial=0.0, community=0.0, cited=5,
         studiness=0.7, fascination=0.4, age=7):
    """A synthetic candidate with the fields the fusion getters read."""
    return {"doi": doi, "publicity": publicity, "editorial": editorial,
            "community": community, "cited": cited, "studiness": studiness,
            "fascination": fascination, "age": age,
            "venue_type": "journal", "journal": "Test Journal"}


def ranks(candidates, weights):
    ranked = sorted(fuse([dict(c) for c in candidates], weights),
                    key=lambda w: w["score"], reverse=True)
    return [w["doi"] for w in ranked]


def jaccard(a, b):
    sa, sb = set(a), set(b)
    return round(len(sa & sb) / len(sa | sb), 3) if sa | sb else 1.0


def collapsed_equal(doi):
    """A single release and three syndicated copies must give the same signal."""
    one = cluster_releases([Release("eurekalert", "Paper X", doi=doi)])
    three = cluster_releases([
        Release("eurekalert", "Paper X", doi=doi),
        Release("sciencedaily", "Paper X"),
        Release("physorg", "Paper X"),
    ])
    return publicity_value(one[0]), publicity_value(three[0])


def main():
    corpus = [
        work("no-signal"),
        work("publicized", publicity=1.0),
        work("editorial", editorial=1.0),
        work("both", publicity=1.0, editorial=1.0),
        work("high-impact", cited=400),
        work("fascinating", fascination=1.0),
    ]
    baseline = ranks(corpus, SIGNAL_WEIGHTS)
    no_publicity = ranks(corpus, {**SIGNAL_WEIGHTS, "publicity": 0.0})

    top3 = baseline[:3]
    perturbations = {}
    for label, factor in (("publicity_x0.5", 0.5), ("publicity_x1.5", 1.5)):
        weights = {**SIGNAL_WEIGHTS, "publicity": round(SIGNAL_WEIGHTS["publicity"] * factor, 3)}
        perturbations[label] = {"top3_jaccard": jaccard(top3, ranks(corpus, weights)[:3])}

    one, three = collapsed_equal("10.1/x")
    # Presence signals must not weaken as the corpus grows: one publicized paper among
    # 200 otherwise-identical ones still gets its full boost, not a tie-tail sliver.
    scale = [work(f"filler-{i}") for i in range(200)] + [work("one-publicized", publicity=1.0)]
    scale_ranked = ranks(scale, SIGNAL_WEIGHTS)
    scale_scores = {w["doi"]: w["score"] for w in fuse([dict(c) for c in scale], SIGNAL_WEIGHTS)}
    margin = round(scale_scores["one-publicized"] - scale_scores["filler-0"], 5)
    full_boost = round(SIGNAL_WEIGHTS["publicity"] * (1 / 60), 5)
    report = {
        "weights": SIGNAL_WEIGHTS,
        "weights_sum": round(sum(SIGNAL_WEIGHTS.values()), 3),
        "baseline_order": baseline,
        "publicity_off_order": no_publicity,
        "checks": {
            "publicized_beats_no_signal": baseline.index("publicized") < baseline.index("no-signal"),
            "editorial_beats_no_signal": baseline.index("editorial") < baseline.index("no-signal"),
            "press_edges_editorial": baseline.index("publicized") < baseline.index("editorial"),
            "publicity_off_drops_publicized": no_publicity.index("publicized") > baseline.index("publicized"),
            "syndication_collapses": one == three == 1.0,
            "stable_at_scale": scale_ranked[0] == "one-publicized" and margin >= full_boost * 0.9,
        },
        "scale_margin": margin,
        "full_boost": full_boost,
        "perturbations": perturbations,
    }
    all_pass = all(report["checks"].values()) and report["weights_sum"] == 1.0
    report["passed"] = all_pass

    print(f"weights sum to {report['weights_sum']}")
    print("baseline order:      ", " > ".join(baseline))
    print("publicity off order: ", " > ".join(no_publicity))
    for name, ok in report["checks"].items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    for name, value in perturbations.items():
        print(f"  {name}: top-3 Jaccard {value['top3_jaccard']}")
    print(f"  scale margin among 200 fillers: {margin} (full boost {full_boost})")
    print("PASSED" if all_pass else "FAILED")

    (HERE / "publicity_effect.json").write_text(json.dumps(report, indent=2))
    print("\nwrote", HERE / "publicity_effect.json")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
