from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from core.models import UserProfile, License, CHAUFFEcoinTransaction, Order
from .forms import EmailUserCreationForm, EmailAuthenticationForm


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
    
    # Get user's licenses
    licenses = License.objects.filter(user=request.user).select_related('order__product').order_by('-issued_at')
    
    # Get recent CHAUFFEcoin transactions
    transactions = CHAUFFEcoinTransaction.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    # Get user's orders
    orders = Order.objects.filter(user=request.user).select_related('product').order_by('-created_at')[:5]
    
    return render(request, 'accounts/profile.html', {
        'user': request.user,
        'user_profile': user_profile,
        'licenses': licenses,
        'transactions': transactions,
        'orders': orders,
        'title': 'My Account - My Chauffe'
    })
