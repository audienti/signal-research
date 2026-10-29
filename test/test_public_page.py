import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('page', ROOT / 'skills/signal-prospect-research/scripts/read_public_page.py')
page = importlib.util.module_from_spec(spec); spec.loader.exec_module(page)

class PublicPageTests(unittest.TestCase):
    def test_nested_graph_links_and_dates(self):
        obj={'@graph':[{'@type':['Thing','JobPosting'],'title':'AE','datePosted':'2020-01-01','validThrough':'2021-01-01','description':'<p>Manager <a href="/people/a">Alex</a></p>'}]}
        result=page.extract('<script type="application/ld+json">'+json.dumps(obj)+'</script>','https://example.com/jobs/1')
        job=result['jobs'][0]
        self.assertEqual(job['descriptionLinks'][0]['url'],'https://example.com/people/a')
        self.assertEqual(job['validThrough'],'2021-01-01')
        self.assertEqual(job['openStatus'],'unverified')
        self.assertEqual(job['jsonPath'],'jsonld[0].@graph[0]')

    def test_malformed_json_is_diagnostic_not_negative(self):
        result=page.extract('<script type="application/ld+json">broken</script>','https://example.com')
        self.assertEqual(result['jobs'],[]); self.assertEqual(len(result['parseErrors']),1)

    def test_listing_state_must_match_url_and_identifier(self):
        base='<script type="application/ld+json">'+json.dumps({'@type':'JobPosting','identifier':{'value':'123'}})+'</script>'
        state='<script>window.__appData = '+json.dumps({'posting':{'id':'123','isListed':False}})+';</script>'
        same=page.extract(base+state,'https://jobs.ashbyhq.com/company/123')['jobs'][0]
        self.assertFalse(same['listingState']['isListed'])
        for url in ['https://jobs.ashbyhq.com/company/456','https://example.com/company/123']:
            self.assertNotIn('listingState',page.extract(base+state,url)['jobs'][0])

    def test_script_never_enters_visible_text(self):
        result=page.extract('<script>secret()</script><style>hidden</style><p>Evidence</p>','https://example.com')
        self.assertEqual(result['text'],'Evidence')

if __name__=='__main__': unittest.main()
