from __future__ import annotations
import sys, unittest
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from core import load_terms
from simulations import SIM_TITLES, SIM_SUBJECTS

class FinalExpansionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.terms=load_terms()
    def test_final_counts(self):
        c=Counter(t.get('subject') for t in self.terms)
        self.assertGreaterEqual(len(self.terms),2000)
        self.assertGreaterEqual(c['수학'],850)
        self.assertGreaterEqual(c['화학'],250)
        self.assertGreaterEqual(c['생명과학'],170)
        self.assertGreaterEqual(c['지구과학'],120)
        self.assertGreaterEqual(c['천문학'],60)
    def test_100_simulators(self):
        self.assertEqual(len(SIM_TITLES),100)
        self.assertEqual(set(SIM_TITLES),set(SIM_SUBJECTS))
        # The 3.1.6 wrapper adds three new models; every one of the original
        # 100 models must still be linked by the original 50,000 cards.
        linked={t.get('simulator') for t in self.terms[:50000] if t.get('simulator')}
        self.assertEqual(set(SIM_TITLES),linked)
    def test_science_search(self):
        names={t['name_ko'] for t in self.terms}
        for name in ['보일 법칙','세포막','판 구조론','케플러 제3법칙','리만 제타 함수']:
            self.assertIn(name,names)

if __name__=='__main__': unittest.main()
