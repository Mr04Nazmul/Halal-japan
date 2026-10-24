import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from japan_ingredient_barcodes import jan_valid

class JanBarcodeValidation(unittest.TestCase):
    def test_valid_jan8(self):
        self.assertTrue(jan_valid("45123283"))
        self.assertTrue(jan_valid("45117053"))
    def test_valid_jan13(self):
        self.assertTrue(jan_valid("4901002090142"))
        self.assertTrue(jan_valid("4901002118198"))
    def test_invalid_or_unsupported(self):
        for value in (None,"","45123284","4901002090143","１２３４５６７８","012345678901","01234567890123","1234567","abc12345"):
            with self.subTest(value=value):
                self.assertFalse(jan_valid(value))
if __name__=="__main__":
    unittest.main()
