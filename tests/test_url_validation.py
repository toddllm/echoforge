#!/usr/bin/env python
"""
URL Validation Security Test for EchoForge

This script tests the URL validation function that prevents open redirect vulnerabilities.
"""

import os
import sys
import logging
from app.core.security import validate_redirect_url

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("url_validation_test")

def test_url_validation():
    """Test the URL validation function with various URLs."""
    logger.info("=" * 80)
    logger.info("TESTING URL VALIDATION FUNCTION")
    logger.info("=" * 80)
    
    # Test cases - format: (input_url, allowed_hosts, expected_result)
    test_cases = [
        # Relative URLs (should be allowed)
        ("/dashboard", None, "/dashboard"),
        ("/users/profile", None, "/users/profile"),
        ("/", None, "/"),
        
        # Protocol-relative URLs (should be blocked)
        ("//evil.com/hack", None, None),
        
        # Absolute URLs with no allowed hosts (should be blocked)
        ("http://example.com", None, None),
        ("https://legit-site.com", None, None),
        
        # Absolute URLs with allowed hosts (should be allowed if host matches)
        ("http://example.com", ["example.com"], "http://example.com"),
        ("https://legit-site.com", ["legit-site.com"], "https://legit-site.com"),
        ("https://evil.com", ["example.com", "legit-site.com"], None),
        
        # Malicious URLs (should be blocked)
        ("javascript:alert(1)", None, None),
        ("data:text/html,<script>alert(1)</script>", None, None),
        
        # Edge cases
        (None, None, None),
        ("", None, None),
        ("  ", None, None),
        ("../../../etc/passwd", None, None),
    ]
    
    # Run all test cases
    passed = 0
    failed = 0
    
    for i, (input_url, allowed_hosts, expected) in enumerate(test_cases):
        result = validate_redirect_url(input_url, allowed_hosts)
        
        if result == expected:
            logger.info(f"✅ Test case {i+1}: PASS - Input: '{input_url}', Allowed hosts: {allowed_hosts}, Result: '{result}'")
            passed += 1
        else:
            logger.error(f"❌ Test case {i+1}: FAIL - Input: '{input_url}', Allowed hosts: {allowed_hosts}, Expected: '{expected}', Got: '{result}'")
            failed += 1
    
    # Summary
    logger.info("=" * 80)
    logger.info(f"TOTAL: {passed + failed}, PASSED: {passed}, FAILED: {failed}")
    logger.info("=" * 80)
    
    return failed == 0

if __name__ == "__main__":
    result = test_url_validation()
    sys.exit(0 if result else 1)
