#!/usr/bin/env python3
"""
Test runner for telegram-language-buddy-bot
Runs all unit tests and integration tests
"""

import unittest
import sys
import os
import time

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# Add tests to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))


def run_all_tests():
    """Run all tests and return results"""
    # Discover and load all test modules
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Add test modules
    test_modules = [
        'test_language_detector',
        'test_free_translator',
        'test_database',
        'test_telegram_bot',
        'test_bot_controller',
        'test_integration'
    ]
    
    for module_name in test_modules:
        try:
            # Import directly from current directory
            module = __import__(module_name, fromlist=['*'])
            tests = test_loader.loadTestsFromModule(module)
            test_suite.addTests(tests)
            print(f"✓ Loaded tests from {module_name}")
        except ImportError as e:
            print(f"✗ Failed to load {module_name}: {e}")
        except Exception as e:
            print(f"✗ Error loading {module_name}: {e}")
    
    # Run tests
    test_runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True,
        failfast=False
    )
    
    print(f"\n{'='*60}")
    print("RUNNING TESTS")
    print(f"{'='*60}")
    
    start_time = time.time()
    result = test_runner.run(test_suite)
    end_time = time.time()
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    print(f"Time taken: {end_time - start_time:.2f} seconds")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    # Return success/failure
    return len(result.failures) == 0 and len(result.errors) == 0


def run_specific_test(test_name):
    """Run a specific test class or method"""
    test_loader = unittest.TestLoader()
    
    # Try to load the specific test
    try:
        if '.' in test_name:
            # Specific test method
            module_name, class_name, method_name = test_name.rsplit('.', 2)
            module = __import__(module_name, fromlist=[class_name])
            test_class = getattr(module, class_name)
            test_suite = test_loader.loadTestsFromName(method_name, test_class)
        else:
            # Test class
            module_name, class_name = test_name.rsplit('.', 1)
            module = __import__(module_name, fromlist=[class_name])
            test_class = getattr(module, class_name)
            test_suite = test_loader.loadTestsFromTestCase(test_class)
        
        test_runner = unittest.TextTestRunner(verbosity=2)
        result = test_runner.run(test_suite)
        return len(result.failures) == 0 and len(result.errors) == 0
        
    except (ImportError, AttributeError) as e:
        print(f"Error loading test {test_name}: {e}")
        return False


def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        print(f"Running specific test: {test_name}")
        success = run_specific_test(test_name)
    else:
        # Run all tests
        success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
