# -*- coding: utf-8 -*-
"""Content regression tests: preservation, authored cards and Korean quiz search."""
import hashlib
import json
import sys
import unittest
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from korean_study import filter_korean_terms, evaluate_answer, source_label
from core import _prepare_term_for_search, search_terms


class ContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads((ROOT / 'data/terms.json').read_text(encoding='utf-8'))
        cls.terms = cls.doc['terms']
        cls.baseline = json.loads((ROOT / 'tests/content_baseline.json').read_text(encoding='utf-8'))
        cls.korean = [t for t in cls.terms if t['subject'] == '국어']
        cls.physics = [t for t in cls.terms if t['id'].startswith('curated-316-')]
        cls.quiz_doc = json.loads((ROOT/'data/korean_quizzes.json').read_text(encoding='utf-8'))
        cls.sources = {s['id']:s for s in json.loads((ROOT/'data/sources.json').read_text(encoding='utf-8'))['sources']}

    def test_every_original_term_field_and_id_is_preserved(self):
        original = self.terms[:self.baseline['original_count']]
        canonical = json.dumps(original, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
        self.assertEqual(hashlib.sha256(canonical).hexdigest(), self.baseline['canonical_sha256'])
        self.assertEqual(len(original), 50000)
        self.assertEqual(sum(t.get('tier') == '확장 인덱스' for t in original), 47637)
        self.assertEqual(sum(t.get('tier') != '확장 인덱스' for t in original), 2363)

    def test_exact_inventory_and_unique_new_names(self):
        self.assertEqual(self.doc['version'], '3.1.6')
        self.assertEqual(self.doc['count'], len(self.terms))
        self.assertEqual(len(self.terms), 50078)
        self.assertEqual(len(self.physics), 36)
        self.assertEqual(len(self.korean), 42)
        self.assertEqual(len({t['id'] for t in self.terms}), len(self.terms))
        old_names = {t['name_ko'] for t in self.terms[:50000]}
        new_names = [t['name_ko'] for t in self.terms[50000:]]
        self.assertEqual(len(new_names), len(set(new_names)))
        self.assertFalse(old_names.intersection(new_names))

    def test_authored_content_has_concrete_explanation_example_and_caution(self):
        for term in self.physics + self.korean:
            with self.subTest(term=term['id']):
                self.assertGreaterEqual(len(term['detail']), 70)
                self.assertGreaterEqual(len(term['example']), 20)
                self.assertGreaterEqual(len(term['caution']), 20)
                self.assertIn(term['example'], term['search_text'])
                self.assertIn(term['caution'], term['search_text'])
                self.assertNotIn('\ufffd', json.dumps(term, ensure_ascii=False))
                self.assertEqual(term['curation_version'], '3.1.6')
                self.assertTrue(term['sources'])
                for source_id in term['sources']:
                    self.assertIn(source_id,self.sources)
                    url=self.sources[source_id]['url']
                    self.assertEqual(urlparse(url).scheme, 'https')
                    self.assertIn(urlparse(url).hostname,
                                  ('openstax.org','korean.go.kr','stdict.korean.go.kr','ncic.re.kr'))

    def test_korean_covers_all_six_areas(self):
        areas = Counter(t['category'] for t in self.korean)
        self.assertEqual(set(areas), {'국어 · 문법','국어 · 문학','국어 · 읽기','국어 · 쓰기','국어 · 듣기·말하기','국어 · 매체'})
        self.assertEqual(areas, {'국어 · 문법':15,'국어 · 문학':11,'국어 · 읽기':6,'국어 · 쓰기':5,'국어 · 듣기·말하기':3,'국어 · 매체':2})

    def test_every_korean_card_has_valid_quiz_and_feedback(self):
        quizzes = self.quiz_doc['items']
        self.assertEqual(self.quiz_doc['version'], '3.1.6')
        self.assertEqual(self.quiz_doc['count'], 42)
        self.assertEqual({q['term_id'] for q in quizzes}, {t['id'] for t in self.korean})
        self.assertEqual(len({q['term_id'] for q in quizzes}), len(quizzes))
        answer_positions = set()
        for quiz in quizzes:
            with self.subTest(term=quiz['term_id']):
                self.assertEqual(len(quiz['choices']), 3)
                self.assertEqual(len(set(quiz['choices'])), 3)
                self.assertIn(quiz['answer_index'], range(3))
                self.assertTrue(quiz['question'])
                self.assertTrue(quiz['feedback'])
                answer_positions.add(quiz['answer_index'])
                for index in range(3):
                    correct, message = evaluate_answer(quiz,index)
                    self.assertEqual(correct,index == quiz['answer_index'])
                    self.assertIn(quiz['feedback'],message)
                    if not correct:
                        self.assertIn(quiz['choices'][quiz['answer_index']],message)
                with self.assertRaises(ValueError):
                    evaluate_answer(quiz,-1)
        self.assertEqual(answer_positions,{0,1,2})

    def test_korean_search_by_title_area_example_and_initials(self):
        self.assertEqual(filter_korean_terms(self.terms,'피동 표현')[0]['id'],'korean-316-passive')
        self.assertEqual(len(filter_korean_terms(self.terms,'','문법')),15)
        self.assertTrue(all(t['category']=='국어 · 문학' for t in filter_korean_terms(self.terms,'','문학')))
        self.assertIn('korean-316-digital-communication',{t['id'] for t in filter_korean_terms(self.terms,'공개 범위')})
        self.assertIn('korean-316-phoneme',{t['id'] for t in filter_korean_terms(self.terms,'ㅇㅇ')})
        self.assertEqual(filter_korean_terms(self.terms,'없는용어xyz'),[])

    def test_normal_dictionary_search_can_find_korean_and_deeper_physics(self):
        prepared = [_prepare_term_for_search(dict(t)) for t in self.korean+self.physics]
        self.assertEqual(search_terms(prepared,'피동 표현')[0]['id'],'korean-316-passive')
        self.assertEqual(search_terms(prepared,'시간 상수')[0]['id'],'curated-316-rc-time-constant')
        self.assertIn('curated-316-static-friction-limit',{t['id'] for t in search_terms(prepared,'한계값')})

    def test_new_simulation_links_exist(self):
        from enhanced_simulations import ENHANCED_TITLES
        from simulations import SIM_TITLES
        known=set(ENHANCED_TITLES)|set(SIM_TITLES)
        for term in self.physics:
            if term['simulator']:
                self.assertIn(term['simulator'],known,term['id'])

    def test_reference_labels_identify_official_sources(self):
        self.assertIn('국립국어원',source_label('https://stdict.korean.go.kr/main/main.do'))
        self.assertIn('교육과정',source_label('https://ncic.re.kr/?query=2022'))


if __name__ == '__main__':
    unittest.main()
