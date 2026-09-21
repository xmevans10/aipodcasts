import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from publicity import (Release, cluster_releases, editorial_value, event_index,
                       publicity_value)

DOI = "10.1371/journal.pone.0000001"


class ClusterTests(unittest.TestCase):
    def test_syndicated_copies_collapse_to_one_event(self):
        events = cluster_releases([
            Release("eurekalert", "A hidden young crater on the Moon", doi=DOI),
            Release("sciencedaily", "A hidden young crater on the Moon"),
            Release("physorg", "A hidden young crater on the Moon"),
        ])
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].sources, {"eurekalert", "sciencedaily", "physorg"})
        self.assertEqual(events[0].doi, DOI)
        self.assertTrue(events[0].press)
        self.assertFalse(events[0].independent)

    def test_one_publicity_signal_regardless_of_syndicator_count(self):
        one = cluster_releases([Release("eurekalert", "Paper X", doi=DOI)])
        three = cluster_releases([
            Release("eurekalert", "Paper X", doi=DOI),
            Release("sciencedaily", "Paper X"),
            Release("physorg", "Paper X"),
        ])
        self.assertEqual(publicity_value(one[0]), publicity_value(three[0]))

    def test_independent_outlet_is_its_own_signal(self):
        events = cluster_releases([
            Release("eurekalert", "A surprise Moon crater", doi=DOI),
            Release("quanta", "A surprise Moon crater"),
        ])
        self.assertEqual(len(events), 1)
        self.assertTrue(events[0].press)
        self.assertTrue(events[0].independent)
        self.assertEqual(editorial_value(events[0]), 1.0)

    def test_syndicated_only_does_not_count_as_independent(self):
        events = cluster_releases([
            Release("sciencedaily", "Sleep and memory", doi=DOI),
            Release("physorg", "Sleep and memory"),
        ])
        self.assertTrue(events[0].is_syndicated_only)
        self.assertEqual(editorial_value(events[0]), 0.0)
        self.assertEqual(publicity_value(events[0]), 0.0)

    def test_fuzzy_title_merges_releases_without_doi(self):
        events = cluster_releases([
            Release("eurekalert", "Ancient DNA reveals a lost horse lineage", doi=DOI),
            Release("sciencedaily", "Ancient DNA reveals a lost horse lineage"),
        ])
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].doi, DOI)

    def test_different_papers_stay_separate(self):
        events = cluster_releases([
            Release("eurekalert", "A hidden young crater on the Moon", doi=DOI),
            Release("eurekalert", "Gut microbes shape sleep quality", doi="10.1371/journal.pone.0000002"),
        ])
        self.assertEqual(len(events), 2)

    def test_event_index_only_includes_resolved_dois(self):
        events = cluster_releases([
            Release("eurekalert", "Paper with DOI", doi=DOI),
            Release("sciencedaily", "An entirely unrelated sleep study"),
        ])
        index = event_index(events)
        self.assertEqual(set(index), {DOI})
        self.assertEqual(index[DOI].sources, {"eurekalert"})


if __name__ == "__main__":
    unittest.main()
