"""
Profile Data Caching Service
Provides intelligent caching for CloudManager profile data with smart invalidation.
"""

import hashlib
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from django.core.cache import cache
from django.conf import settings
from django.contrib.auth.models import User

from core.models import UserProfile, Order
from core.services.cloudmanager_client import get_cloudmanager_client

logger = logging.getLogger(__name__)


class ProfileCacheService:
    """Service for caching user profile data from CloudManager"""
    
    CACHE_VERSION = "v1.0.0"  # Update when cache structure changes
    
    @classmethod
    def _get_cache_key(cls, user_id: int) -> str:
        """Generate cache key for user profile data"""
        return f"profile_data:{cls.CACHE_VERSION}:user_{user_id}"
    
    @classmethod
    def _get_cache_meta_key(cls, user_id: int) -> str:
        """Generate cache key for cache metadata"""
        return f"profile_meta:{cls.CACHE_VERSION}:user_{user_id}"
    
    @classmethod
    def _get_user_cache_hash(cls, user: User) -> str:
        """Generate hash based on user's purchase data to detect changes"""
        user_profile = getattr(user, 'profile', None)
        if not user_profile:
            return "no_profile"
        
        # Include data that would trigger cache invalidation
        cache_data = {
            'total_licenses_purchased': user_profile.total_licenses_purchased,
            'completed_orders_count': Order.objects.filter(
                user=user, 
                status='completed'
            ).count(),
            'last_completed_order': Order.objects.filter(
                user=user, 
                status='completed'
            ).order_by('-updated_at').values_list('updated_at', flat=True).first()
        }
        
        # Convert datetime to string for JSON serialization
        if cache_data['last_completed_order']:
            cache_data['last_completed_order'] = cache_data['last_completed_order'].isoformat()
        
        # Create hash of cache data
        cache_json = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_json.encode()).hexdigest()[:16]
    
    @classmethod
    def get_cached_profile_data(cls, user: User) -> Optional[Dict[str, Any]]:
        """
        Get cached profile data for user if still valid
        
        Returns:
            Dict with cached data or None if cache miss/invalid
        """
        cache_key = cls._get_cache_key(user.id)
        meta_key = cls._get_cache_meta_key(user.id)
        
        # Get cached data and metadata
        cached_data = cache.get(cache_key)
        cached_meta = cache.get(meta_key)
        
        if not cached_data or not cached_meta:
            logger.info(f"Cache miss for user {user.id}")
            return None
        
        # Check if user's purchase data has changed
        current_hash = cls._get_user_cache_hash(user)
        cached_hash = cached_meta.get('user_hash')
        
        if current_hash != cached_hash:
            logger.info(f"Cache invalidated for user {user.id} - purchase data changed")
            cls.invalidate_user_cache(user.id)
            return None
        
        # Check cache age (additional safety check)
        cache_age = (datetime.now(timezone.utc) - cached_meta['cached_at']).total_seconds()
        max_age = getattr(settings, 'PROFILE_CACHE_TIMEOUT', 3600)
        
        if cache_age > max_age:
            logger.info(f"Cache expired for user {user.id} after {cache_age}s")
            cls.invalidate_user_cache(user.id)
            return None
        
        logger.info(f"Cache hit for user {user.id} - age: {cache_age:.1f}s")
        return cached_data
    
    @classmethod
    def cache_profile_data(cls, user: User, profile_data: Dict[str, Any]) -> None:
        """
        Cache profile data for user with metadata
        
        Args:
            user: Django user object
            profile_data: Profile data to cache (blockchain summary, etc.)
        """
        cache_key = cls._get_cache_key(user.id)
        meta_key = cls._get_cache_meta_key(user.id)
        timeout = getattr(settings, 'PROFILE_CACHE_TIMEOUT', 3600)
        
        # Create metadata
        cache_meta = {
            'user_hash': cls._get_user_cache_hash(user),
            'cached_at': datetime.now(timezone.utc),
            'cache_version': cls.CACHE_VERSION
        }
        
        # Cache both data and metadata
        cache.set(cache_key, profile_data, timeout)
        cache.set(meta_key, cache_meta, timeout)
        
        logger.info(f"Cached profile data for user {user.id}")
    
    @classmethod
    def invalidate_user_cache(cls, user_id: int) -> None:
        """Force invalidate cache for specific user"""
        cache_key = cls._get_cache_key(user_id)
        meta_key = cls._get_cache_meta_key(user_id)
        
        cache.delete(cache_key)
        cache.delete(meta_key)
        
        logger.info(f"Invalidated cache for user {user_id}")
    
    @classmethod
    def invalidate_user_cache_by_user(cls, user: User) -> None:
        """Force invalidate cache for user object"""
        cls.invalidate_user_cache(user.id)
    
    @classmethod
    def get_or_fetch_profile_data(cls, user: User) -> Dict[str, Any]:
        """
        Get profile data from cache or fetch fresh from CloudManager
        
        Returns:
            Dict containing blockchain summary and metadata
        """
        # Try cache first
        cached_data = cls.get_cached_profile_data(user)
        if cached_data:
            return cached_data
        
        # Cache miss - fetch from CloudManager
        logger.info(f"Fetching fresh profile data for user {user.id}")
        
        # Get or create user profile
        user_profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={'chauffecoins_balance': 0}
        )
        
        # Get CloudManager client and fetch data
        cloudmanager_client = get_cloudmanager_client()
        user_uuid = user_profile.get_uuid_string()
        
        # Fetch blockchain data from CloudManager API
        blockchain_data = cloudmanager_client.get_user_blockchain_summary(user_uuid)
        cloudmanager_health = cloudmanager_client.get_health()
        
        # Initialize default values
        blockchain_summary = {
            'total_blockchains': 0,
            'total_blocks': 0,
            'total_transactions': 0,
            'total_chauffecoins': 0,
            'controller_names': [],
            'dloid_parameters': []
        }
        blockchain_error = None
        
        if blockchain_data.get('success'):
            blockchain_summary = blockchain_data.get('summary', blockchain_summary)
        else:
            blockchain_error = blockchain_data.get('error', 'Unknown error fetching blockchain data')
        
        # Prepare data for caching
        profile_data = {
            'blockchain_summary': blockchain_summary,
            'blockchain_error': blockchain_error,
            'cloudmanager_health': cloudmanager_health,
            'connection_error': blockchain_data.get('connection_error', False),
            'timeout_error': blockchain_data.get('timeout_error', False),
            'fetch_timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Cache the data
        cls.cache_profile_data(user, profile_data)
        
        return profile_data
    
    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """Get caching statistics (for debugging/monitoring)"""
        # Note: Django's LocMemCache doesn't provide detailed stats
        # This is a placeholder for future cache backend upgrades
        return {
            'cache_backend': settings.CACHES['default']['BACKEND'],
            'cache_version': cls.CACHE_VERSION,
            'cache_timeout': getattr(settings, 'PROFILE_CACHE_TIMEOUT', 3600)
        }


# Signal handlers to invalidate cache when orders are completed
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import Order

@receiver(post_save, sender=Order)
def invalidate_user_cache_on_order_change(sender, instance, **kwargs):
    """Invalidate user's profile cache when order status changes"""
    if instance.status == 'completed':
        ProfileCacheService.invalidate_user_cache_by_user(instance.user)
        logger.info(f"Invalidated profile cache for user {instance.user.id} due to completed order {instance.id}")