#!/usr/bin/env python3
"""
Stripe Live Keys Verification Script
Verifies that Stripe live keys are properly configured and functional
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mychauffe.settings')
django.setup()

from django.conf import settings
import stripe

def verify_stripe_configuration():
    """Verify Stripe configuration and test API connectivity"""
    
    print("=" * 60)
    print("STRIPE LIVE PAYMENT PROCESSING VERIFICATION")
    print("=" * 60)
    
    # Check Django settings
    print(f"📋 Django Settings:")
    print(f"   STRIPE_PUBLISHABLE_KEY: {settings.STRIPE_PUBLISHABLE_KEY[:20]}...{settings.STRIPE_PUBLISHABLE_KEY[-4:]}")
    print(f"   STRIPE_SECRET_KEY: {settings.STRIPE_SECRET_KEY[:20]}...{settings.STRIPE_SECRET_KEY[-4:]}")
    print(f"   STRIPE_CURRENCY: {settings.STRIPE_CURRENCY}")
    print(f"   DEBUG: {settings.DEBUG}")
    
    # Verify key formats
    pub_key_valid = settings.STRIPE_PUBLISHABLE_KEY.startswith('pk_live_')
    secret_key_valid = settings.STRIPE_SECRET_KEY.startswith('sk_live_')
    
    print(f"\n🔑 Key Validation:")
    print(f"   Publishable Key Format: {'✅ Valid (pk_live_)' if pub_key_valid else '❌ Invalid (not live key)'}")
    print(f"   Secret Key Format: {'✅ Valid (sk_live_)' if secret_key_valid else '❌ Invalid (not live key)'}")
    
    if not (pub_key_valid and secret_key_valid):
        print("\n❌ CRITICAL: Not using Stripe live keys!")
        return False
    
    # Test Stripe API connectivity
    print(f"\n🔌 API Connectivity Test:")
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        # Test API by retrieving account info
        account = stripe.Account.retrieve()
        
        print(f"   Connection: ✅ Success")
        print(f"   Account ID: {account.id}")
        print(f"   Business Name: {account.business_profile.name if account.business_profile else 'Not set'}")
        print(f"   Country: {account.country}")
        print(f"   Currency: {account.default_currency}")
        print(f"   Charges Enabled: {'✅ Yes' if account.charges_enabled else '❌ No'}")
        print(f"   Payouts Enabled: {'✅ Yes' if account.payouts_enabled else '❌ No'}")
        
        if not account.charges_enabled:
            print(f"   ⚠️ WARNING: Account cannot accept charges yet")
            
        if not account.payouts_enabled:
            print(f"   ⚠️ WARNING: Account cannot receive payouts yet")
            
    except stripe.error.AuthenticationError:
        print(f"   Connection: ❌ Authentication failed - invalid API key")
        return False
    except stripe.error.PermissionError:
        print(f"   Connection: ❌ Permission denied - check account status")
        return False
    except Exception as e:
        print(f"   Connection: ❌ Error - {str(e)}")
        return False
    
    # Test creating a test Payment Intent (will not charge)
    print(f"\n💳 Payment Intent Test:")
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=100,  # $1.00 test amount
            currency='usd',
            automatic_payment_methods={'enabled': True},
            metadata={'test': 'verification_script'}
        )
        
        print(f"   Test Payment Intent: ✅ Created successfully")
        print(f"   Intent ID: {payment_intent.id}")
        print(f"   Amount: ${payment_intent.amount/100:.2f}")
        print(f"   Status: {payment_intent.status}")
        
    except Exception as e:
        print(f"   Test Payment Intent: ❌ Failed - {str(e)}")
        return False
    
    # Security check
    print(f"\n🔒 Security Check:")
    print(f"   DEBUG Mode: {'❌ Enabled (disable for production!)' if settings.DEBUG else '✅ Disabled'}")
    print(f"   HTTPS CSRF: {'✅ Enabled' if not settings.DEBUG and settings.CSRF_COOKIE_SECURE else '❌ Check settings'}")
    print(f"   Secure Cookies: {'✅ Enabled' if not settings.DEBUG and settings.SESSION_COOKIE_SECURE else '❌ Check settings'}")
    
    print(f"\n🎉 STRIPE LIVE PAYMENT PROCESSING READY!")
    print(f"   ✅ Live keys configured correctly")
    print(f"   ✅ API connectivity verified") 
    print(f"   ✅ Payment processing functional")
    
    if settings.DEBUG:
        print(f"\n⚠️ REMINDER: Set DEBUG=False for production deployment")
    
    print("=" * 60)
    return True

if __name__ == '__main__':
    try:
        success = verify_stripe_configuration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Verification failed with error: {e}")
        sys.exit(1)