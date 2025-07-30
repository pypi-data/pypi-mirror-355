import unittest
from textminer.cleaner import remove_stopwords, extract_keywords

class TestCleaner(unittest.TestCase):
    def test_remove_stopwords(self):
        text = "This is a sample text with some stopwords"
        result = remove_stopwords(text)
        self.assertNotIn("is", result.lower())
        self.assertNotIn("a", result.lower())
        self.assertIn("sample", result.lower())
    
    def test_extract_keywords(self):
        text = "Python is a programming language. Python is very popular for data science."
        keywords = extract_keywords(text, top_n=3)
        self.assertTrue(len(keywords) <= 3)
        self.assertTrue(isinstance(keywords, list))

if __name__ == '__main__':
    unittest.main()