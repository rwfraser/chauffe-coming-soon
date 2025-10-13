from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from functools import wraps


def profile_required(view_func):
    """
    Decorator to check if user has completed their profile (first_name and last_name).
    Redirects to profile page if profile is incomplete.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        # Check if user has both first and last name
        if not request.user.first_name or not request.user.last_name:
            messages.warning(
                request, 
                'Please complete your profile by adding your first and last name before accessing the store. '
                'Your name will be used for DLO license generation and cannot be changed after purchase.'
            )
            return redirect('accounts:profile')
        
        # Profile is complete, proceed with the original view
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def profile_required_ajax(view_func):
    """
    Decorator for AJAX views to check if user has completed their profile.
    Returns JSON error response if profile is incomplete.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        from django.http import JsonResponse
        
        # Check if user has both first and last name
        if not request.user.first_name or not request.user.last_name:
            return JsonResponse({
                'success': False,
                'error': 'Profile incomplete',
                'message': 'Please complete your profile by adding your first and last name before making purchases.',
                'redirect_url': '/accounts/profile/'
            }, status=400)
        
        # Profile is complete, proceed with the original view
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def create_profile_required_template_view(template_name, page_name):
    """
    Create a view that shows a profile completion requirement page.
    """
    @login_required
    def profile_required_view(request):
        # If profile is complete, redirect to the intended page
        if request.user.first_name and request.user.last_name:
            # This shouldn't happen if decorators are working correctly,
            # but provides a fallback
            return redirect('core:store')  # or appropriate redirect
        
        return render(request, 'core/profile_required.html', {
            'title': f'{page_name} - Profile Required',
            'page_name': page_name,
            'user_first_name': request.user.first_name,
            'user_last_name': request.user.last_name,
        })
    
    return profile_required_view