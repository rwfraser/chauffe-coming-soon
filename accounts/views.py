from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from core.models import UserProfile, License, CHAUFFEcoinTransaction, Order
from core.services.cloudmanager_client import get_cloudmanager_client
from .forms import EmailUserCreationForm, EmailAuthenticationForm
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
    
    # Get CloudManager client
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
        logger.info(f"Retrieved blockchain data for user {user_uuid}: {blockchain_summary['total_blockchains']} blockchains")
    else:
        blockchain_error = blockchain_data.get('error', 'Unknown error fetching blockchain data')
        logger.error(f"Failed to fetch blockchain data for user {user_uuid}: {blockchain_error}")
        
        # Add appropriate user message
        if blockchain_data.get('connection_error'):
            messages.warning(request, 
                'CloudManager service is currently unavailable. Blockchain data cannot be displayed.')
        elif blockchain_data.get('timeout_error'):
            messages.warning(request, 
                'CloudManager service is responding slowly. Some data may not be available.')
        else:
            messages.warning(request, 
                f'Unable to fetch blockchain data: {blockchain_error}')
    
    # Keep local data for orders (payment history)
    orders = Order.objects.filter(user=request.user).select_related('product').order_by('-created_at')[:5]
    
    # Keep local transactions for now (could be migrated to CloudManager later)
    transactions = CHAUFFEcoinTransaction.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    return render(request, 'accounts/profile.html', {
        'user': request.user,
        'user_profile': user_profile,
        
        # CloudManager blockchain data
        'blockchain_summary': blockchain_summary,
        'blockchain_data': blockchain_data,
        'blockchain_error': blockchain_error,
        'cloudmanager_health': cloudmanager_health,
        
        # Local data (for now)
        'transactions': transactions,
        'orders': orders,
        
        'title': 'My Account - My Chauffe'
    })
