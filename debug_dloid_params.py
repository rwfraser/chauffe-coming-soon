#!/usr/bin/env python3
"""
Debug script to test DLOID parameter passing and response from CloudManager
"""
import requests
import json
from datetime import datetime

def test_dloid_parameters():
    """Test exact DLOID parameter processing"""
    print("DLOID Parameter Debug Test")
    print("=" * 50)
    
    # Test payload with specific values - similar to what the form sends
    test_params = {
        'firstName': 'Jessica',
        'lastName': 'Thompson',
        'priorDloidQty': '2',  # Existing licenses
        'chauffeQuantity': '0000100000',  # From form
        'partnershipStatus': 'L',  # From form dropdown
        'collateralizable': 'N',  # From form dropdown
        'inheritance': 'Y',  # From form dropdown
        'convertibility': '2',  # From form dropdown
        'rating': '000025000',  # Base rating from form
        'shareEligible': 'N',  # From form dropdown
        'redeemability': 'P'  # From form dropdown
    }
    
    payload = {
        'name': f'Jessica Thompson License #3 Blockchain {datetime.now().strftime("%H%M%S")}',
        'first_name': 'Jessica',
        'last_name': 'Thompson', 
        'existing_licenses': 2,
        'dloid_params': test_params
    }
    
    print("SENDING TO CLOUDMANAGER:")
    print(f"URL: http://localhost:5000/api/blockchains")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()
    print("DLOID Parameters being sent:")
    for key, value in test_params.items():
        print(f"  {key}: '{value}' (length: {len(str(value))})")
    print()
    
    try:
        response = requests.post(
            'http://localhost:5000/api/blockchains',
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"RESPONSE STATUS: {response.status_code}")
        print(f"RESPONSE HEADERS: {dict(response.headers)}")
        print()
        
        if response.status_code in [200, 201]:  # Accept both 200 OK and 201 Created
            try:
                data = response.json()
                print("CLOUDMANAGER RESPONSE:")
                print(json.dumps(data, indent=2))
                print()
                
                # Analyze the returned DLOID params
                if 'dloid_params' in data:
                    dloid_string = data['dloid_params']
                    controller_name = data.get('controller_name', '')
                    print(f"RETURNED DLOID STRING: '{dloid_string}'")
                    print(f"DLOID STRING LENGTH: {len(dloid_string)} chars")
                    print(f"CONTROLLER NAME: '{controller_name}' (length: {len(controller_name)})")
                    print()
                    
                    # Check if DLOID string contains controller name at the start
                    if controller_name and dloid_string.startswith(controller_name):
                        actual_dloid = dloid_string[len(controller_name):]
                        print(f"⚠️ DLOID string contains controller name at start!")
                        print(f"CONTROLLER NAME PART: '{controller_name}'")
                        print(f"ACTUAL DLOID PART: '{actual_dloid}' (length: {len(actual_dloid)})")
                        print()
                        dloid_to_analyze = actual_dloid
                    else:
                        dloid_to_analyze = dloid_string
                    
                    if len(dloid_to_analyze) >= 25:  # At least 25 chars for core DLOID data
                        print(f"ANALYZING DLOID PART: '{dloid_to_analyze}'")
                        print(f"  Chars 1-10:  '{dloid_to_analyze[0:10]}'  (CHAUFFEcoin Quantity)")
                        print(f"  Chars 11-11: '{dloid_to_analyze[10:11] if len(dloid_to_analyze) > 10 else 'N/A'}' (Partnership Status)")
                        print(f"  Chars 12-12: '{dloid_to_analyze[11:12] if len(dloid_to_analyze) > 11 else 'N/A'}' (Collateralizable)")
                        print(f"  Chars 13-13: '{dloid_to_analyze[12:13] if len(dloid_to_analyze) > 12 else 'N/A'}' (Inheritance)")
                        print(f"  Chars 14-14: '{dloid_to_analyze[13:14] if len(dloid_to_analyze) > 13 else 'N/A'}' (Convertibility)")
                        print(f"  Chars 15-23: '{dloid_to_analyze[14:23] if len(dloid_to_analyze) > 22 else 'N/A'}' (Rating)")
                        print(f"  Chars 24-24: '{dloid_to_analyze[23:24] if len(dloid_to_analyze) > 23 else 'N/A'}' (Share Eligible)")
                        print(f"  Chars 25-25: '{dloid_to_analyze[24:25] if len(dloid_to_analyze) > 24 else 'N/A'}' (Redeemability)")
                        if len(dloid_to_analyze) > 25:
                            print(f"  Chars 26+: '{dloid_to_analyze[25:]}' (Reserved/Padding)")
                        print()
                        
                        # Compare with expected values
                        print("COMPARISON WITH SENT VALUES:")
                        if len(dloid_to_analyze) >= 10:
                            expected_qty = test_params['chauffeQuantity']
                            actual_qty = dloid_to_analyze[0:10]
                            print(f"  CHAUFFEcoin Quantity: Expected '{expected_qty}', Got '{actual_qty}' - {'✅' if expected_qty == actual_qty else '❌'}")
                        
                        if len(dloid_to_analyze) >= 11:
                            expected_partnership = test_params['partnershipStatus']
                            actual_partnership = dloid_to_analyze[10:11]
                            print(f"  Partnership Status: Expected '{expected_partnership}', Got '{actual_partnership}' - {'✅' if expected_partnership == actual_partnership else '❌'}")
                        
                        if len(dloid_to_analyze) >= 12:
                            expected_collateral = test_params['collateralizable']
                            actual_collateral = dloid_to_analyze[11:12]
                            print(f"  Collateralizable: Expected '{expected_collateral}', Got '{actual_collateral}' - {'✅' if expected_collateral == actual_collateral else '❌'}")
                        
                        if len(dloid_to_analyze) >= 13:
                            expected_inheritance = test_params['inheritance']
                            actual_inheritance = dloid_to_analyze[12:13]
                            print(f"  Inheritance: Expected '{expected_inheritance}', Got '{actual_inheritance}' - {'✅' if expected_inheritance == actual_inheritance else '❌'}")
                        
                        if len(dloid_to_analyze) >= 14:
                            expected_convertibility = test_params['convertibility']
                            actual_convertibility = dloid_to_analyze[13:14]
                            print(f"  Convertibility: Expected '{expected_convertibility}', Got '{actual_convertibility}' - {'✅' if expected_convertibility == actual_convertibility else '❌'}")
                        
                        if len(dloid_to_analyze) >= 23:
                            expected_rating = test_params['rating']
                            actual_rating = dloid_to_analyze[14:23]
                            print(f"  Rating: Expected '{expected_rating}', Got '{actual_rating}' - {'✅' if expected_rating == actual_rating else '❌'}")
                        
                        if len(dloid_to_analyze) >= 24:
                            expected_share = test_params['shareEligible']
                            actual_share = dloid_to_analyze[23:24]
                            print(f"  Share Eligible: Expected '{expected_share}', Got '{actual_share}' - {'✅' if expected_share == actual_share else '❌'}")
                        
                        if len(dloid_to_analyze) >= 25:
                            expected_redeem = test_params['redeemability']
                            actual_redeem = dloid_to_analyze[24:25]
                            print(f"  Redeemability: Expected '{expected_redeem}', Got '{actual_redeem}' - {'✅' if expected_redeem == actual_redeem else '❌'}")
                        
                    else:
                        print(f"❌ DLOID string has unexpected length: {len(dloid_string)} (expected 57)")
                        print(f"Raw DLOID string: '{dloid_string}'")
                else:
                    print("❌ No 'dloid_params' field in response")
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"Raw response: {response.text}")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to CloudManager on localhost:5000")
        print("Make sure CloudManager.py is running")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_dloid_parameters()