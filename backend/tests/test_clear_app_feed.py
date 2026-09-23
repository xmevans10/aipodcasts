import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from clear_app_feed import load_exclusions, published_dois, wipe_app  # noqa: E402


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
                "https://pub-e19f5de621fd4b4ea01c0465d0251407.r2.dev", 1234,
                exclusions_path)
            self.assertEqual((count, deleted), (1, 2))
            self.assertEqual(client.puts["v1/feed.json"], [])
            self.assertEqual(client.puts["v1/.release/excluded-dois.json"],
                             ["10.1234/old.paper"])
            self.assertEqual(client.puts["v1/.release/baseline.json"]["minimum_run_id"], 1234)
            self.assertEqual(client.listed_prefixes, ["v1/audio/", "v1/episodes/"])
            self.assertEqual(json.loads(exclusions_path.read_text()), ["10.1234/old.paper"])

    def test_exclusion_ledger_adds_prior_feed_dois(self):
        client = FakeS3([])
        client.puts["v1/.release/excluded-dois.json"] = ["10.1234/old"]
        self.assertEqual(published_dois([{"sources": [
            {"url": "https://doi.org/10.5678/New"}]}]), {"10.5678/new"})


if __name__ == "__main__":
    unittest.main()
