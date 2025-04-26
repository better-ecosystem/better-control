#!/usr/bin/env python3

import os
import sys
import unittest
import argparse

def discover_and_run_tests(verbosity=1, pattern="test_*.py"):
    """Discover and run all tests in the tests directory."""
    # Get the directory where this file is located
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add the src directory to the path so modules can be imported
    sys.path.insert(0, os.path.abspath(os.path.join(test_dir, "..", "src")))
    
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=test_dir, pattern=pattern)
    
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    # Return appropriate exit code
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Better Control tests")
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")
    parser.add_argument("-p", "--pattern", type=str, default="test_*.py", 
                        help="Pattern to match test files (default: test_*.py)")
    args = parser.parse_args()
    
    verbosity = 2 if args.verbose else 1
    sys.exit(discover_and_run_tests(verbosity, args.pattern))