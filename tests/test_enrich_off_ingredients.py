import gzip, importlib.util, json, tempfile, unittest
from pathlib import Path
path=Path(__file__).resolve().parents[1]/"scripts"/"enrich_off_ingredients.py"
spec=importlib.util.spec_from_file_location("enrichment",path)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class EnrichIngredientTests(unittest.TestCase):
 def setup_fixture(self,root):
  d=root/"data";(d/"world-food-shards").mkdir(parents=True)
  jp={"license":"ODbL-1.0","products":[{"code":"4900000000001","product_name":"A","ingredients_text":"","_halalVerified":False}]}
  shards={"license":"ODbL-1.0","records":[
   {"code":"4900000000002","product_name":"B","ingredients_text":"","_halalVerified":False},
   {"code":"4900000000003","product_name":"C","ingredients_text":"米","_halalVerified":False}]}
  man={"license":"ODbL-1.0","total_unique_records":3,"japan_original_records":1,"additional_with_ingredient_text":1}
  (d/"openfoodfacts-japan.json").write_text(json.dumps(jp))
  (d/"world-food-shards"/"490.json").write_text(json.dumps(shards))
  (d/"food-catalog-manifest.json").write_text(json.dumps(man))
  source=root/"off.tsv.gz"
  source.write_bytes(gzip.compress(
   "code\tingredients_text\tingredients_text_ja\n"
   "4900000000001\trice\t米、食塩\n"
   "4900000000002\tN/A\t小麦粉、砂糖\n"
   "4900000000003\tchanged\t肉\n"
   "0000000000001\tpork\t豚肉\n".encode()))
  return source

 def test_recovers_exact_code_without_overwriting(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);src=self.setup_fixture(root)
   a=mod.run(root,src)
   self.assertEqual((a["new_ingredient_texts"],a["with_ingredient_text_after"],a["new_japan_texts"]),(2,3,1))
   p=json.loads((root/"data/world-food-shards/490.json").read_text())["records"]
   self.assertEqual(p[0]["ingredients_text"],"小麦粉、砂糖")
   self.assertEqual(p[1]["ingredients_text"],"米")
   self.assertFalse(p[0]["_halalVerified"])
   self.assertFalse(p[0]["_ingredientsVerified"])
   b=mod.run(root,src)
   self.assertEqual(b["new_ingredient_texts"],0)

 def test_rejects_barcode_duplication(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);src=self.setup_fixture(root)
   path=root/"data/world-food-shards/490.json"
   obj=json.loads(path.read_text())
   obj["records"][0]["code"]="4900000000001"
   path.write_text(json.dumps(obj))
   with self.assertRaisesRegex(ValueError,"Duplicate/invalid"):
    mod.run(root,src)
if __name__=="__main__":
 unittest.main()
