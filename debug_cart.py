#!/usr/bin/env python3
"""
Debug script to test the add-to-cart endpoint directly
"""
import requests
import json
import re

# First, get CSRF token from Django
def get_csrf_token():
    """Get CSRF token from Django"""
    try:
        response = requests.get("http://localhost:8000/store/")
        if response.status_code == 200:
            # Extract CSRF token from HTML
            match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.text)
            if match:
                return match.group(1)
            # Try cookies as fallback
            csrf_cookie = response.cookies.get('csrftoken')
            return csrf_cookie
    except Exception as e:
        print(f"Error getting CSRF token: {e}")
    return None

print("Getting CSRF token...")
csrf_token = get_csrf_token()
print(f"CSRF Token: {csrf_token[:20] + '...' if csrf_token else 'None'}")

# Test the add-to-cart endpoint
url = "http://localhost:8000/api/add-to-cart/"
headers = {
    'Content-Type': 'application/json',
}

if csrf_token:
    headers['X-CSRFToken'] = csrf_token

# Test payload
payload = {
    "product_id": 1,
    "quantity": 1
}

print("Testing add-to-cart endpoint...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print("-" * 50)

try:
    response = requests.post(url, json=payload, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Raw Response: {repr(response.text)}")
    
    if response.headers.get('content-type', '').startswith('application/json'):
        try:
            data = response.json()
            print(f"JSON Response: {json.dumps(data, indent=2)}")
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
    else:
        print(f"Response Content-Type: {response.headers.get('content-type', 'Unknown')}")
        print("Response is not JSON - likely HTML error page")
        if len(response.text) > 500:
            print(f"Response (first 500 chars): {response.text[:500]}...")
        else:
            print(f"Full Response: {response.text}")
            
except requests.exceptions.ConnectionError:
    print("ERROR: Cannot connect to Django server.")
    print("Make sure Django server is running on localhost:8000")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")