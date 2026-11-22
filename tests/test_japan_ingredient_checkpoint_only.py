import json,sqlite3,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from crawl_japanese_ingredients import Collector,checkpoint_only

class CheckpointOnlyTests(unittest.TestCase):
 def test_finalizer_skips_constructor_migrations_and_preserves_pending_queue(self):
  with tempfile.TemporaryDirectory() as folder:
   c=Collector(folder,100000)
   url='https://housefoods.jp/products/special/legacy-campaign/'
   c.db.execute("INSERT OR IGNORE INTO queue(url,status,attempts,next_try,error) VALUES(?,'pending',0,0,NULL)",(url,))
   c.db.execute("DELETE FROM metadata WHERE key='legacy_marketing_navigation_quarantine_20261122_v1'")
   c.db.commit()
   c.db.close()

   checkpoint_only(folder,100000)

   db=sqlite3.connect(Path(folder)/'state.sqlite3')
   row=db.execute('SELECT status,error FROM queue WHERE url=?',(url,)).fetchone()
   migration=db.execute("SELECT value FROM metadata WHERE key='legacy_marketing_navigation_quarantine_20261122_v1'").fetchone()
   db.close()
   self.assertEqual(row,('pending',None))
   self.assertIsNone(migration)
   summary=json.loads((Path(folder)/'summary.json').read_text())
   self.assertEqual(summary['accepted_ingredient_products'],0)
   self.assertFalse(summary['halal_certification_performed'])

if __name__=='__main__':unittest.main()
