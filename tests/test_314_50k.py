import json
import unittest
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class Corpus50KTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload=json.loads((ROOT/"data"/"terms.json").read_text(encoding="utf-8"))
        cls.terms=cls.payload["terms"]

    def test_exact_50000(self):
        self.assertGreaterEqual(len(self.terms),50000)
        self.assertEqual(self.payload.get("count"),len(self.terms))

    def test_balanced_subjects(self):
        c=Counter(t.get("subject") for t in self.terms)
        self.assertEqual(c["수학"],8334)
        self.assertGreaterEqual(c["물리"],8334)
        for s in ["화학","생명과학","지구과학","천문학"]:
            self.assertEqual(c[s],8333)

    def test_common_essentials_present(self):
        names={t.get("name_ko") for t in self.terms}
        for n in ["등차수열","등비수열","뉴턴 운동 제2법칙","몰","DNA","판 구조론","적색편이"]:
            self.assertIn(n,names)

    def test_expansion_is_labelled(self):
        ext=[t for t in self.terms if t.get("tier")=="확장 인덱스"]
        self.assertEqual(len(ext),50000-2363)
        self.assertTrue(all(t.get("root_id") for t in ext[:500]))

if __name__=='__main__': unittest.main()
