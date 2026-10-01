import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from clear_app_feed import current_exclusions, load_exclusions, published_dois, wipe_app  # noqa: E402
from daily_release import app_feed_url


class FakePaginator:
    def __init__(self, client):
        self.client = client

    def paginate(self, **kwargs):
        self.client.listed_prefixes.append(kwargs["Prefix"])
        return [{"Contents": [{"Key": kwargs["Prefix"] + "old.m4a"}]}]


class FakeS3:
    def __init__(self, feed):
        self.feed = feed
        self.puts = {}
        self.deletes = []
        self.listed_prefixes = []

    def get_object(self, **kwargs):
        if kwargs["Key"] == "v1/feed.json":
            return {"Body": io.BytesIO(json.dumps(self.feed).encode())}
        if kwargs["Key"] in self.puts:
            return {"Body": io.BytesIO(json.dumps(self.puts[kwargs["Key"]]).encode())}
        error = RuntimeError("missing")
        error.response = {"Error": {"Code": "NoSuchKey"}}
        raise error

    def put_object(self, **kwargs):
        self.puts[kwargs["Key"]] = json.loads(kwargs["Body"])

    def get_paginator(self, _name):
        return FakePaginator(self)

    def delete_objects(self, **kwargs):
        self.deletes.extend(item["Key"] for item in kwargs["Delete"]["Objects"])


class ClearAppFeedTests(unittest.TestCase):
    def test_wipe_hides_episodes_and_preserves_a_net_new_baseline(self):
        feed = [{"id": "old-id", "hostID": "fern", "sources": [
            {"url": "https://doi.org/10.1234/Old.Paper"}]}]
        client = FakeS3(feed)
        with tempfile.TemporaryDirectory() as tmp:
            exclusions_path = Path(tmp) / "excluded.json"
            count, deleted = wipe_app(
                client, "episodes", "v1",
                "https://staging.example", 1234,
                exclusions_path)
            self.assertEqual((count, deleted), (1, 3))
            self.assertEqual(client.puts["v1/feed.json"], [])
            self.assertEqual(client.puts["v1/.release/excluded-dois.json"],
                             ["10.1234/old.paper"])
            self.assertEqual(client.puts["v1/.release/baseline.json"]["minimum_run_id"], 1234)
            self.assertEqual(client.listed_prefixes, ["v1/audio/", "v1/episodes/", "v1/listen/"])
            self.assertEqual(json.loads(exclusions_path.read_text()), ["10.1234/old.paper"])

    def test_live_feed_reset_is_rejected_before_any_writes(self):
        client = FakeS3([])
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "Refusing to wipe the live"):
                wipe_app(client, "episodes", "v1", app_feed_url().removesuffix("/v1/feed.json"),
                         1234, Path(tmp) / "excluded.json")
        self.assertEqual(client.puts, {})
        self.assertEqual(client.deletes, [])

    def test_exclusion_ledger_adds_prior_feed_dois(self):
        client = FakeS3([])
        client.puts["v1/.release/excluded-dois.json"] = ["10.1234/old"]
        self.assertEqual(published_dois([{"sources": [
            {"url": "https://doi.org/10.5678/New"}]}]), {"10.5678/new"})


    def test_generation_excludes_live_papers_as_well_as_retired_papers(self):
        client = FakeS3([])
        client.puts['v1/.release/excluded-dois.json'] = ['10.1234/old']
        client.feed = [{'sources': [{'url': 'https://doi.org/10.5678/Live'}]}]
        self.assertEqual(current_exclusions(client, 'bucket', 'v1'), ['10.1234/old', '10.5678/live'])


if __name__ == "__main__":
    unittest.main()
