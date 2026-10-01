import hashlib
import io
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from staging_release_drill import drill
from withdraw_episode import encode


class StorageError(Exception):
    def __init__(self, code):
        self.response = {'Error': {'Code': code}}


class MemoryStorage:
    def __init__(self):
        self.objects = {}; self.writes = []

    def get_object(self, Bucket, Key):
        if Key not in self.objects: raise StorageError('NoSuchKey')
        data = self.objects[Key]
        return {'Body': io.BytesIO(data), 'ETag': hashlib.sha256(data).hexdigest()}

    def head_object(self, Bucket, Key):
        return self.get_object(Bucket, Key)

    def put_object(self, Bucket, Key, Body, IfMatch=None, **kwargs):
        if IfMatch and (Key not in self.objects or hashlib.sha256(self.objects[Key]).hexdigest() != IfMatch):
            raise StorageError('PreconditionFailed')
        self.objects[Key] = Body; self.writes.append(Key)

    def copy_object(self, Bucket, Key, CopySource, **kwargs):
        self.objects[Key] = self.objects[CopySource['Key']]; self.writes.append(Key)

    def delete_object(self, Bucket, Key):
        self.objects.pop(Key, None); self.writes.append(Key)


class StagingDrillTests(unittest.TestCase):
    @patch.dict(os.environ, {'R2_PREFIX': 'v1'})
    def test_drill_withdraws_and_restores_without_mutating_live_keys(self):
        storage = MemoryStorage(); base = 'https://cdn.example'
        story = {'id': 'episode-abc', 'title': 'T', 'body': 'Actual science.', 'hostID': 'nova',
                 'published': '2026-10-01', 'audioURL': base + '/v1/audio/abc.m4a',
                 'detailURL': base + '/v1/episodes/abc.json',
                 'shareURL': base + '/v1/listen/episode-abc.html'}
        storage.objects.update({'v1/feed.json': encode([story]), 'v1/audio/abc.m4a': b'audio',
                                'v1/episodes/abc.json': encode({'story': story}),
                                'v1/listen/episode-abc.html': b'original page'})
        original = dict(storage.objects)
        result = drill(storage, 'bucket', base, '123')
        self.assertTrue(result['snapshotRollbackPassed'])
        self.assertTrue(result['conditionalWriteRejected'])
        self.assertTrue(all(k.startswith('v1-release-drill/123/') for k in storage.writes))
        self.assertTrue(all(storage.objects[k] == v for k,v in original.items()))
        self.assertEqual(storage.objects['v1-release-drill/123/audio/abc.m4a'], b'audio')

    def test_non_numeric_run_cannot_select_an_arbitrary_storage_prefix(self):
        with self.assertRaises(ValueError):
            drill(MemoryStorage(), 'bucket', 'https://cdn.example', '../v1')
