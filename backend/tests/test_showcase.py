import copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from showcase import check

class ShowcaseChecks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        script='word '*400
        self.data={'status':'private_preview_not_published','tts_model':'eleven_multilingual_v2','max_total_characters':9000,'max_generation_attempts':3,'episodes':[]}
        for name in ['mira','clara','elias']:
            (self.root/(name+'.txt')).write_text(script)
            self.data['episodes'].append({'id':name,'script_file':name+'.txt','script_sha256':hashlib.sha256(script.encode()).hexdigest(),'character_count':len(script),'sources':[{'url':'https://example.com/paper','authors':['Author']} ]})
        self.path=self.root/'manifest.json'
    def tearDown(self):self.tmp.cleanup()
    def run_check(self):self.path.write_text(json.dumps(self.data));return check(self.path)
    def test_valid_preview(self):self.assertEqual(self.run_check()[1],6000)
    def test_rejects_script_changed_after_review(self):
        (self.root/'mira.txt').write_text('altered script')
        with self.assertRaisesRegex(ValueError,'changed since source review'):self.run_check()
    def test_rejects_excess_budget(self):
        self.data['max_total_characters']=5000
        with self.assertRaisesRegex(ValueError,'budget exceeded'):self.run_check()
    def test_rejects_production_publication(self):
        self.data['status']='published'
        with self.assertRaisesRegex(ValueError,'private review'):self.run_check()
    def test_rejects_path_escape(self):
        self.data['episodes'][0]['script_file']='../outside.txt'
        with self.assertRaisesRegex(ValueError,'beside manifest'):self.run_check()
    def test_requires_attribution(self):
        self.data['episodes'][0]['sources'][0]['authors']=[]
        with self.assertRaisesRegex(ValueError,'attribution'):self.run_check()

if __name__=='__main__':unittest.main()
