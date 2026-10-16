import copy
import datetime as dt
import io
import unittest
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

from test_withdraw_episode import episode, BASE
from withdraw_episode import encode, fingerprint
from adopt_editorial_catalog import make_plan, apply
import editorial_policy


class EditorialAdoptionTests(unittest.TestCase):
    def setUp(self):
        self.day = dt.datetime.now(ZoneInfo('America/New_York')).date().isoformat()
        self.old = episode()
        self.incoming = []
        for name, host in [('brain', 'ada'), ('galaxy', 'jax')]:
            story = episode(name)
            doi = '10.1234/' + name
            story.update(hostID=host, published=self.day, sources=[{'url': 'https://doi.org/' + doi}])
            story['editorialPolicy'] = editorial_policy.stamp(story, {
                'selection_policy': editorial_policy.SELECTION, 'host': host, 'doi': doi,
                'routing': {'host': host, 'doi': doi, 'version': 'source-question-routing-v1'},
                'major_sources': [{'doi': doi, 'source': 'science', 'match': 'explicit_doi',
                                   'url': 'https://www.science.org/content/article/' + name}]})
            self.incoming.append(story)
        self.plan = make_plan([self.old], self.incoming, self.day, 123)

    def test_preserves_old_identity_with_notice_and_requires_current_recordings(self):
        old = next(s for s in self.plan['feed'] if s['id'] == self.old['id'])
        self.assertIsNone(old['audioURL'])
        self.assertIn('editorial update', old['withdrawalNotice'])
        self.assertEqual(len([s for s in self.plan['feed'] if s.get('withdrawalNotice') is None]), 2)
        self.assertIsNotNone(self.old['audioURL'])
        bad = copy.deepcopy(self.incoming)
        bad[0]['body'] = 'Unreviewed changes'
        with self.assertRaisesRegex(ValueError, 'stale'):
            make_plan([self.old], bad, self.day, 123)

    def client(self):
        client = Mock()
        client.get_object.return_value = {'Body': io.BytesIO(encode([self.old])), 'ETag': 'etag'}
        return client

    @patch('adopt_editorial_catalog.verify_staged_assets')
    def test_backups_precede_atomic_feed_change_and_public_cleanup(self, verify):
        client = self.client()
        result = apply(client, 'bucket', 'v1', BASE, self.plan, fingerprint(self.plan))
        calls = client.mock_calls
        feed = next(i for i, c in enumerate(calls) if c[0] == 'put_object' and c.kwargs['Key'] == 'v1/feed.json')
        self.assertEqual(calls[feed].kwargs['IfMatch'], 'etag')
        self.assertTrue(all(i < feed for i, c in enumerate(calls) if c[0] == 'copy_object'))
        self.assertTrue(all(i > feed for i, c in enumerate(calls) if c[0] == 'delete_object'))
        self.assertEqual(result['active'], 2)
        verify.assert_called_once_with(self.incoming)

    @patch('adopt_editorial_catalog.verify_staged_assets')
    def test_changed_catalog_or_failed_backup_leaves_live_catalog_untouched(self, _verify):
        client = self.client()
        client.get_object.return_value['Body'] = io.BytesIO(encode([episode('other')]))
        with self.assertRaisesRegex(ValueError, 'changed'):
            apply(client, 'bucket', 'v1', BASE, self.plan, fingerprint(self.plan))
        client.put_object.assert_not_called()
        client = self.client()
        client.copy_object.side_effect = RuntimeError('Backup failed')
        with self.assertRaisesRegex(RuntimeError, 'Backup failed'):
            apply(client, 'bucket', 'v1', BASE, self.plan, fingerprint(self.plan))
        self.assertFalse(any(c.kwargs['Key'] == 'v1/feed.json' for c in client.put_object.call_args_list))
        client.delete_object.assert_not_called()

    def test_edited_plan_is_rejected_before_network(self):
        client = Mock()
        with self.assertRaisesRegex(ValueError, 'fingerprint'):
            apply(client, 'bucket', 'v1', BASE, self.plan, 'wrong')
        client.get_object.assert_not_called()
