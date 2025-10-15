#!/usr/bin/env python3
"""
Complete diagnostic script for add-to-cart issue
"""
import requests
import json
import re
from urllib.parse import urljoin

BASE_URL = "http://localhost:8000"
STORE_URL = urljoin(BASE_URL, "/store/")
ADD_TO_CART_URL = urljoin(BASE_URL, "/api/add-to-cart/")

def get_csrf_token_and_cookies():
    """Get CSRF token and session cookies from the store page"""
    print("=== Step 1: Getting CSRF token from store page ===")
    try:
        response = requests.get(STORE_URL)
        print(f"Store page status: {response.status_code}")
        
        if response.status_code == 200:
            # Look for CSRF token in HTML
            csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.text)
            if csrf_match:
                csrf_token = csrf_match.group(1)
            else:
                # Try meta tag
                csrf_match = re.search(r'name="csrf-token" content="([^"]+)"', response.text)
                csrf_token = csrf_match.group(1) if csrf_match else None
            
            # Get cookies
            cookies = response.cookies
            csrf_cookie = cookies.get('csrftoken')
            session_cookie = cookies.get('sessionid')
            
            print(f"CSRF token from HTML: {csrf_token[:20] + '...' if csrf_token else 'Not found'}")
            print(f"CSRF token from cookie: {csrf_cookie[:20] + '...' if csrf_cookie else 'Not found'}")
            print(f"Session cookie: {session_cookie[:20] + '...' if session_cookie else 'Not found'}")
            print(f"All cookies: {list(cookies.keys())}")
            
            return csrf_token or csrf_cookie, cookies
        else:
            print(f"Failed to load store page: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return None, None
            
    except Exception as e:
        print(f"Error getting CSRF token: {e}")
        return None, None

def test_add_to_cart(csrf_token, cookies):
    """Test the add-to-cart endpoint"""
    print("\n=== Step 2: Testing add-to-cart endpoint ===")
    
    headers = {
        'Content-Type': 'application/json',
        'Referer': STORE_URL,
        'X-Requested-With': 'XMLHttpRequest',  # Mark as AJAX
    }
    
    if csrf_token:
        headers['X-CSRFToken'] = csrf_token
    
    payload = {
        "product_id": 1,
        "quantity": 1
    }
    
    print(f"URL: {ADD_TO_CART_URL}")
    print(f"Headers: {headers}")
    print(f"Payload: {payload}")
    print(f"Cookies: {dict(cookies) if cookies else 'None'}")
    
    try:
        response = requests.post(
            ADD_TO_CART_URL, 
            json=payload, 
            headers=headers, 
            cookies=cookies
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Content-Type: {response.headers.get('content-type', 'Unknown')}")
        
        # Check if response is JSON or HTML
        content_type = response.headers.get('content-type', '').lower()
        
        if 'application/json' in content_type:
            try:
                data = response.json()
                print(f"JSON Response: {json.dumps(data, indent=2)}")
                return True, "Success - JSON response received"
            except json.JSONDecodeError as e:
                print(f"JSON Decode Error: {e}")
                print(f"Raw Response: {repr(response.text[:500])}")
                return False, f"JSON decode error: {e}"
        else:
            print("Response is HTML/Text, not JSON:")
            print(f"First 500 chars: {response.text[:500]}")
            
            # Look for common Django error patterns
            if "403 Forbidden" in response.text or response.status_code == 403:
                return False, "403 Forbidden - Likely CSRF token issue"
            elif "404 Not Found" in response.text or response.status_code == 404:
                return False, "404 Not Found - URL routing issue"
            elif "500 Internal Server Error" in response.text or response.status_code == 500:
                return False, "500 Internal Server Error - Server-side error"
            elif "<html" in response.text.lower():
                return False, f"HTML response received (status {response.status_code}) - Expected JSON"
            else:
                return False, f"Unexpected response type (status {response.status_code})"
                
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False, f"Request exception: {e}"

def test_without_csrf():
    """Test without CSRF token to see what error we get"""
    print("\n=== Step 3: Testing without CSRF token ===")
    
    headers = {
        'Content-Type': 'application/json',
    }
    
    payload = {
        "product_id": 1,
        "quantity": 1
    }
    
    try:
        response = requests.post(ADD_TO_CART_URL, json=payload, headers=headers)
        print(f"Status without CSRF: {response.status_code}")
        print(f"Response snippet: {response.text[:200]}")
        
        if response.status_code == 403:
            return "CSRF protection is working (403 without token)"
        else:
            return f"Unexpected status without CSRF: {response.status_code}"
            
    except Exception as e:
        return f"Error testing without CSRF: {e}"

def main():
    print("Django Add-to-Cart Diagnostic Tool")
    print("=" * 50)
    
    # Step 1: Get CSRF token
    csrf_token, cookies = get_csrf_token_and_cookies()
    
    # Step 2: Test add-to-cart with proper credentials
    if csrf_token and cookies:
        success, message = test_add_to_cart(csrf_token, cookies)
        print(f"\nResult: {message}")
    else:
        print("\nCannot test add-to-cart - no CSRF token or cookies obtained")
    
    # Step 3: Test without CSRF to confirm protection is working
    csrf_test_result = test_without_csrf()
    print(f"\nCSRF Test: {csrf_test_result}")
    
    print("\n" + "=" * 50)
    print("DIAGNOSIS COMPLETE")
    
    if csrf_token and cookies:
        if success:
            print("✅ Add-to-cart endpoint is working correctly!")
            print("The issue may be in the browser JavaScript or browser cache.")
            print("Try:")
            print("1. Clear browser cache completely")
            print("2. Hard refresh (Ctrl+F5)")
            print("3. Use browser dev tools to inspect the actual request being made")
        else:
            print("❌ Add-to-cart endpoint has issues:")
            print(f"   {message}")
            print("Check Django server logs for more details.")
    else:
        print("❌ Could not obtain CSRF token - Django server may not be running")
        print("Make sure Django server is running on http://localhost:8000")

if __name__ == "__main__":
    main()