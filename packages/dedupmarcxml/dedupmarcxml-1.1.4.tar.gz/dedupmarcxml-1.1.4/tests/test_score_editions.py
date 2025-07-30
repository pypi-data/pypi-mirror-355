import unittest

from dedupmarcxml.score.editions import *

class TestScorePublishers(unittest.TestCase):

    def test_normalize_editions(self):
        ed = normalize_edition('17. Auflage, Originalausgabe')
        self.assertEqual(ed, '17;17. AUFLAGE ORIGINALAUSGABE')

        ed = normalize_edition('First Edition 1996')
        self.assertEqual(ed, '1;1996;1 EDITION 1996')

        ed = normalize_edition('Nachdr. der 2. vermehrten Aufl., Leipzig 1854 stattdessen auf dem Originaltitel unzutreffend 1853')
        self.assertEqual(ed, '2;1853;1854;NACHDR. DER 2. VERMEHRTEN AUFL. LEIPZIG 1854 STATTDESSEN AUF DEM ORIGINALTITEL UNZUTREFFEND 1853')

        ed = normalize_edition('Harrison\'s edition')
        self.assertEqual(ed, 'HARRISON S EDITION')

    def test_evaluate_norm_editions(self):
        score = evaluate_norm_editions([17], [16])
        self.assertLess(score, 0.1)

        score = evaluate_norm_editions([17], [17])
        self.assertGreater(score, 0.9)
