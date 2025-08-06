#!/usr/bin/env python3
"""
Test script to check what language codes googletrans returns
"""

from src.models.free_translator import FreeTranslator

def test_language_detection():
    translator = FreeTranslator()
    
    # Test Hebrew text
    hebrew_text = "מה שלומך גיבור"
    detected_he = translator.detect_language(hebrew_text)
    print(f"Hebrew text '{hebrew_text}' -> detected as: {detected_he}")
    
    # Test Russian text
    russian_text = "Привет"
    detected_ru = translator.detect_language(russian_text)
    print(f"Russian text '{russian_text}' -> detected as: {detected_ru}")
    
    # Test English text
    english_text = "Hello"
    detected_en = translator.detect_language(english_text)
    print(f"English text '{english_text}' -> detected as: {detected_en}")

if __name__ == "__main__":
    test_language_detection() 