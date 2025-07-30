import unittest
from textminer.detector import detect_language, detect_languages_with_probability

class TestDetector(unittest.TestCase):
    def test_detect_english(self):
        # ���� ���� �׽�Ʈ
        text = "This is an English text for language detection testing."
        lang = detect_language(text)
        self.assertEqual(lang, "en")
    
    # �ٸ� �׽�Ʈ ���̽���...
