"""
Mock googletrans module for testing
"""

class MockTranslator:
    """Mock Translator class for testing"""
    
    def __init__(self):
        self.translate_called = False
        self.detect_called = False
    
    def translate(self, text, dest=None, src=None):
        """Mock translate method"""
        self.translate_called = True
        self.translate_args = {'text': text, 'dest': dest, 'src': src}
        
        # Return mock result
        result = MockTranslateResult()
        result.text = f"Translated: {text}"
        return result
    
    def detect(self, text):
        """Mock detect method"""
        self.detect_called = True
        self.detect_args = {'text': text}
        
        # Return mock detection result
        result = MockDetectResult()
        result.lang = 'en'
        return result


class MockTranslateResult:
    """Mock translation result"""
    def __init__(self):
        self.text = ""


class MockDetectResult:
    """Mock detection result"""
    def __init__(self):
        self.lang = "en"


# Create a global instance for testing
Translator = MockTranslator
