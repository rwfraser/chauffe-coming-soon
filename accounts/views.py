from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.http import JsonResponse
from core.models import UserProfile, License, CHAUFFEcoinTransaction, Order
from core.services.cloudmanager_client import get_cloudmanager_client
from .forms import EmailUserCreationForm, EmailAuthenticationForm
from .cache_service import ProfileCacheService
import logging


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    form_class = EmailAuthenticationForm
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('core:dashboard')


def register(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
        
    if request.method == 'POST':
        form = EmailUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            # Log the user in after registration
            user = authenticate(username=username, password=form.cleaned_data.get('password1'))
            if user:
                login(request, user)
                return redirect('core:dashboard')
    else:
        form = EmailUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    logger = logging.getLogger(__name__)
    
    # Get or create user profile
    user_profile, created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'chauffecoins_balance': 0}
    )
    
    # Handle profile update
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        
        if first_name and last_name:
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.save()
            messages.success(request, 'Your profile has been updated successfully!')
        else:
            messages.error(request, 'Both first name and last name are required.')
        
        return redirect('accounts:profile')
    
    # Use cached data for immediate page load - AJAX endpoint will handle fresh data
    blockchain_summary = {
        'total_blockchains': 0,
        'total_blocks': 0,
        'total_transactions': 0,
        'total_chauffecoins': 0,
        'controller_names': [],
        'dloid_parameters': []
    }
    
    # Try to get cached data for immediate display (optional)
    try:
        cached_data = ProfileCacheService.get_cached_profile_data(request.user)
        if cached_data and cached_data.get('blockchain_summary'):
            blockchain_summary = cached_data['blockchain_summary']
            logger.info(f"Using cached data for immediate profile display - user {request.user.id}")
    except Exception as e:
        logger.warning(f"Error loading cached data for profile page: {e}")
    
    # Keep local data for orders (payment history)
    orders = Order.objects.filter(user=request.user).select_related('product').order_by('-created_at')[:5]
    
    # Keep local transactions for now (could be migrated to CloudManager later)
    transactions = CHAUFFEcoinTransaction.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    return render(request, 'accounts/profile.html', {
        'user': request.user,
        'user_profile': user_profile,
        
        # Initial empty blockchain data - will be loaded via AJAX
        'blockchain_summary': blockchain_summary,
        
        # Local data (loads immediately)
        'transactions': transactions,
        'orders': orders,
        
        'title': 'My Account - My Chauffe'
    })


@login_required
def get_blockchain_data(request):
    """AJAX endpoint to fetch CloudManager blockchain data with caching"""
    logger = logging.getLogger(__name__)
    
    try:
        # Use the caching service to get data
        profile_data = ProfileCacheService.get_or_fetch_profile_data(request.user)
        
        return JsonResponse({
            'success': not profile_data.get('blockchain_error'),
            'blockchain_summary': profile_data['blockchain_summary'],
            'blockchain_error': profile_data.get('blockchain_error'),
            'cloudmanager_health': profile_data['cloudmanager_health'],
            'connection_error': profile_data.get('connection_error', False),
            'timeout_error': profile_data.get('timeout_error', False),
            'cached': True,  # Indicate this data came through caching system
            'fetch_timestamp': profile_data.get('fetch_timestamp')
        })
        
    except Exception as e:
        logger.error(f"Error in get_blockchain_data for user {request.user.id}: {e}")
        return JsonResponse({
            'success': False,
            'blockchain_summary': {
                'total_blockchains': 0,
                'total_blocks': 0,
                'total_transactions': 0,
                'total_chauffecoins': 0,
                'controller_names': [],
                'dloid_parameters': []
            },
            'blockchain_error': f'Error loading profile data: {str(e)}',
            'cloudmanager_health': {'success': False},
            'connection_error': True,
            'timeout_error': False,
            'cached': False
        })


@login_required
def cache_management(request):
    """Cache management endpoint for debugging and manual cache control"""
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'invalidate':
            ProfileCacheService.invalidate_user_cache_by_user(request.user)
            messages.success(request, 'Profile cache invalidated successfully.')
        elif action == 'fetch_fresh':
            ProfileCacheService.invalidate_user_cache_by_user(request.user)
            ProfileCacheService.get_or_fetch_profile_data(request.user)
            messages.success(request, 'Fresh profile data fetched and cached.')
        
        return redirect('accounts:cache_management')
    
    # Get cache stats and info
    cache_stats = ProfileCacheService.get_cache_stats()
    cached_data = ProfileCacheService.get_cached_profile_data(request.user)
    
    context = {
        'title': 'Profile Cache Management',
        'cache_stats': cache_stats,
        'has_cached_data': cached_data is not None,
        'cached_data_preview': cached_data.get('blockchain_summary', {}) if cached_data else {},
        'fetch_timestamp': cached_data.get('fetch_timestamp') if cached_data else None
    }
    
    return render(request, 'accounts/cache_management.html', context)
