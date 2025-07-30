import unittest
from textminer.detector import detect_language

class TestDetector(unittest.TestCase):
    def test_detect_english(self):
        text = "This is a sample English text for language detection."
        result = detect_language(text)
        self.assertEqual(result, 'en')
    
    def test_detect_korean(self):
        text = "이것은 한국어 텍스트입니다."
        result = detect_language(text)
        self.assertEqual(result, 'ko')

if __name__ == '__main__':
    unittest.main()