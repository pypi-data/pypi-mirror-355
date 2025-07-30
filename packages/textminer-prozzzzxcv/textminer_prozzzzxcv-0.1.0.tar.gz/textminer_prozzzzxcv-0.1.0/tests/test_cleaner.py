import unittest
from textminer.cleaner import remove_stopwords

class TestCleaner(unittest.TestCase):
    def test_remove_stopwords_english(self):
        # ���� �ؽ�Ʈ �׽�Ʈ
        text = "This is a test sentence with some stopwords."
        result = remove_stopwords(text)
        
        # �ҿ� ���ŵǾ����� Ȯ��
        self.assertNotIn("this", result)
        self.assertNotIn("is", result)
        self.assertNotIn("a", result)
        self.assertNotIn("with", result)
        self.assertNotIn("some", result)
        
        # �߿� �ܾ�� �����Ǿ����� Ȯ��
        self.assertIn("test", result)
        self.assertIn("sentence", result)
        self.assertIn("stopwords", result)
    
    # �ٸ� �׽�Ʈ ���̽���...
