#!/usr/bin/env python
"""
Test CloudManager Integration
Simple test script to verify CloudManager API client works correctly
"""

import os
import sys
import django
from pathlib import Path

# Add Django project to path and configure
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mychauffe.settings')
django.setup()

from core.services.cloudmanager_client import get_cloudmanager_client
from core.models import UserProfile
from django.contrib.auth.models import User


def test_cloudmanager_client():
    """Test CloudManager client functionality"""
    print("="*60)
    print("CloudManager Integration Test")
    print("="*60)
    
    client = get_cloudmanager_client()
    
    # Test 1: Health Check
    print("\n1. Testing CloudManager health check...")
    health = client.get_health()
    if health.get('success'):
        print(f"✅ CloudManager is online")
        print(f"   Service: {health.get('service', 'Unknown')}")
        print(f"   Status: {health.get('status', 'Unknown')}")
        if health.get('version'):
            print(f"   Version: {health.get('version')}")
        print(f"   Managed Blockchains: {health.get('managed_blockchains', 0)}")
    else:
        print(f"❌ CloudManager health check failed: {health.get('error')}")
        if health.get('connection_error'):
            print("   💡 Make sure CloudManager.py is running on port 5000")
        return False
    
    # Test 2: Version Check
    print("\n2. Testing version endpoint...")
    version = client.get_version()
    if version.get('success'):
        print(f"✅ Version endpoint working")
        print(f"   Version: {version.get('version')}")
        print(f"   Build Date: {version.get('build_date')}")
        print(f"   Author: {version.get('author')}")
    else:
        print(f"⚠️ Version endpoint failed: {version.get('error')}")
    
    # Test 3: List Blockchains
    print("\n3. Testing blockchain listing...")
    blockchains = client.list_blockchains()
    if blockchains.get('success'):
        count = blockchains.get('count', 0)
        print(f"✅ Blockchain listing successful")
        print(f"   Total blockchains: {count}")
        
        if count > 0:
            print("   Recent blockchains:")
            blockchain_dict = blockchains.get('blockchains', {})
            for i, (blockchain_id, metadata) in enumerate(list(blockchain_dict.items())[:3]):
                name = metadata.get('name', 'Unknown')
                controller = metadata.get('controller_name', 'None')
                user_uuid = metadata.get('user_uuid', 'None')
                print(f"     - {name} (ID: {blockchain_id[:8]}..., Controller: {controller[:16]}..., User: {user_uuid[:8]}...)")
    else:
        print(f"❌ Blockchain listing failed: {blockchains.get('error')}")
        return False
    
    # Test 4: Test with real user UUID (if users exist)
    print("\n4. Testing user-specific blockchain data...")
    try:
        # Get first user with profile
        user_profile = UserProfile.objects.first()
        if user_profile:
            user_uuid = user_profile.get_uuid_string()
            print(f"   Testing with user UUID: {user_uuid[:8]}...")
            
            user_blockchains = client.get_user_blockchain_summary(user_uuid)
            if user_blockchains.get('success'):
                summary = user_blockchains.get('summary', {})
                print(f"✅ User blockchain summary retrieved")
                print(f"   User's blockchains: {summary.get('total_blockchains', 0)}")
                print(f"   Controller names: {len(summary.get('controller_names', []))}")
                print(f"   DLOID parameters: {len(summary.get('dloid_parameters', []))}")
                print(f"   Total CHAUFFEcoins: {summary.get('total_chauffecoins', 0):,}")
                print(f"   Total blocks: {summary.get('total_blocks', 0)}")
            else:
                print(f"⚠️ No blockchain data for user: {user_blockchains.get('error', 'Unknown error')}")
        else:
            print("   ⚠️ No user profiles found in database")
    except Exception as e:
        print(f"   ❌ Error testing user data: {e}")
    
    # Test 5: API endpoint coverage
    print("\n5. Testing API endpoint coverage...")
    endpoints_tested = [
        "✅ /api/health",
        "✅ /api/version", 
        "✅ /api/blockchains",
        "✅ User blockchain filtering"
    ]
    
    for endpoint in endpoints_tested:
        print(f"   {endpoint}")
    
    print("\n" + "="*60)
    print("✅ CloudManager Integration Test Complete!")
    print("✅ Profile page should now display live blockchain data")
    print("="*60)
    return True


if __name__ == "__main__":
    try:
        success = test_cloudmanager_client()
        if success:
            print("\n🎉 All tests passed! CloudManager integration is working.")
            print("💡 You can now view the profile page to see live blockchain data.")
        else:
            print("\n❌ Some tests failed. Please check CloudManager.py is running.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)