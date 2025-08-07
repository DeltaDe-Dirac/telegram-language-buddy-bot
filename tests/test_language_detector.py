import unittest
from unittest.mock import patch
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models.language_detector import LanguageDetector


class TestLanguageDetector(unittest.TestCase):
    """Test cases for LanguageDetector class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.detector = LanguageDetector()
    
    def test_supported_languages_not_empty(self):
        """Test that SUPPORTED_LANGUAGES contains languages"""
        self.assertGreater(len(LanguageDetector.SUPPORTED_LANGUAGES), 0)
        self.assertIsInstance(LanguageDetector.SUPPORTED_LANGUAGES, dict)
    
    def test_supported_languages_format(self):
        """Test that all language codes are lowercase strings"""
        for code, name in LanguageDetector.SUPPORTED_LANGUAGES.items():
            self.assertIsInstance(code, str)
            self.assertIsInstance(name, str)
            self.assertEqual(code, code.lower())
            self.assertGreater(len(code), 0)
            self.assertGreater(len(name), 0)
    
    def test_get_language_list_format(self):
        """Test that get_language_list returns formatted string"""
        lang_list = LanguageDetector.get_language_list()
        self.assertIsInstance(lang_list, str)
        self.assertGreater(len(lang_list), 0)
        
        # Check that it contains language codes in backticks
        lines = lang_list.split('\n')
        for line in lines:
            if line.strip():
                self.assertIn('`', line)
                self.assertIn(' - ', line)
    
    def test_get_language_list_contains_all_languages(self):
        """Test that get_language_list contains all supported languages"""
        lang_list = LanguageDetector.get_language_list()
        for code, name in LanguageDetector.SUPPORTED_LANGUAGES.items():
            self.assertIn(f"`{code}` - {name}", lang_list)
    
    def test_is_valid_language_valid_codes(self):
        """Test is_valid_language with valid language codes"""
        for code in LanguageDetector.SUPPORTED_LANGUAGES.keys():
            self.assertTrue(LanguageDetector.is_valid_language(code))
            # Test case insensitivity
            self.assertTrue(LanguageDetector.is_valid_language(code.upper()))
            self.assertTrue(LanguageDetector.is_valid_language(code.title()))
    
    def test_is_valid_language_invalid_codes(self):
        """Test is_valid_language with invalid language codes"""
        invalid_codes = ['', 'invalid', 'xx', '123', 'en-us', 'EN_US']
        for code in invalid_codes:
            self.assertFalse(LanguageDetector.is_valid_language(code))
    
    def test_is_valid_language_edge_cases(self):
        """Test is_valid_language with edge cases"""
        # None and non-string inputs
        self.assertFalse(LanguageDetector.is_valid_language(None))
        self.assertFalse(LanguageDetector.is_valid_language(123))
        self.assertFalse(LanguageDetector.is_valid_language([]))
        self.assertFalse(LanguageDetector.is_valid_language({}))
    
    def test_common_languages_present(self):
        """Test that common languages are present in supported languages"""
        common_languages = ['en', 'es', 'fr', 'de', 'ru', 'zh', 'ja', 'ko']
        for lang in common_languages:
            self.assertIn(lang, LanguageDetector.SUPPORTED_LANGUAGES)
    
    def test_language_names_not_empty(self):
        """Test that language names are not empty strings"""
        for code, name in LanguageDetector.SUPPORTED_LANGUAGES.items():
            self.assertIsInstance(name, str)
            self.assertGreater(len(name.strip()), 0)
    
    def test_no_duplicate_language_codes(self):
        """Test that there are no duplicate language codes"""
        codes = list(LanguageDetector.SUPPORTED_LANGUAGES.keys())
        unique_codes = set(codes)
        self.assertEqual(len(codes), len(unique_codes))
    
    def test_no_duplicate_language_names(self):
        """Test that there are no duplicate language names"""
        names = list(LanguageDetector.SUPPORTED_LANGUAGES.values())
        unique_names = set(names)
        self.assertEqual(len(names), len(unique_names))
    
    def test_language_codes_format_consistency(self):
        """Test that all language codes follow consistent format"""
        for code in LanguageDetector.SUPPORTED_LANGUAGES.keys():
            # Should be exactly 2 characters
            self.assertEqual(len(code), 2)
            # Should be alphabetic
            self.assertTrue(code.isalpha())
            # Should be lowercase
            self.assertEqual(code, code.lower())
    
    def test_language_names_format_consistency(self):
        """Test that all language names follow consistent format"""
        for name in LanguageDetector.SUPPORTED_LANGUAGES.values():
            # Should be title case or proper format
            self.assertIsInstance(name, str)
            self.assertGreater(len(name), 0)
            # Should not have leading/trailing whitespace
            self.assertEqual(name, name.strip())
    
    def test_get_language_list_ordering(self):
        """Test that get_language_list maintains consistent ordering"""
        lang_list1 = LanguageDetector.get_language_list()
        lang_list2 = LanguageDetector.get_language_list()
        self.assertEqual(lang_list1, lang_list2)
    
    def test_is_valid_language_whitespace_handling(self):
        """Test that whitespace is handled correctly in language validation"""
        # Test with whitespace around valid codes
        self.assertTrue(LanguageDetector.is_valid_language(' en '))
        self.assertTrue(LanguageDetector.is_valid_language('\ten\t'))
        self.assertTrue(LanguageDetector.is_valid_language('\n en \n'))
        
        # Test with whitespace around invalid codes
        self.assertFalse(LanguageDetector.is_valid_language(' invalid '))
        self.assertFalse(LanguageDetector.is_valid_language('\txx\t'))
    
    def test_is_valid_language_special_characters(self):
        """Test that special characters are handled correctly"""
        special_chars = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '_', '+', '=']
        for char in special_chars:
            self.assertFalse(LanguageDetector.is_valid_language(f'en{char}'))
            self.assertFalse(LanguageDetector.is_valid_language(f'{char}en'))
    
    def test_supported_languages_immutability(self):
        """Test that SUPPORTED_LANGUAGES is not accidentally modified"""
        original_languages = dict(LanguageDetector.SUPPORTED_LANGUAGES)
        
        # Call methods that might modify the dict
        LanguageDetector.get_language_list()
        LanguageDetector.is_valid_language('en')
        
        # Verify the dict hasn't changed
        self.assertEqual(LanguageDetector.SUPPORTED_LANGUAGES, original_languages)
    
    def test_language_detector_singleton_behavior(self):
        """Test that multiple instances behave consistently"""
        detector1 = LanguageDetector()
        detector2 = LanguageDetector()
        
        # Both instances should have access to the same SUPPORTED_LANGUAGES
        self.assertEqual(detector1.SUPPORTED_LANGUAGES, detector2.SUPPORTED_LANGUAGES)
        
        # Both should validate languages the same way
        test_codes = ['en', 'es', 'invalid', 'xx']
        for code in test_codes:
            self.assertEqual(
                LanguageDetector.is_valid_language(code),
                LanguageDetector.is_valid_language(code)
            )


if __name__ == '__main__':
    unittest.main()
