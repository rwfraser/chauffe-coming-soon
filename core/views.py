from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone


def home(request):
    """Coming soon home page"""
    return render(request, 'core/home.html', {
        'title': 'My Chauffe - Coming Soon'
    })


@login_required
def dashboard(request):
    """User dashboard after login"""
    return render(request, 'core/dashboard.html', {
        'title': 'Dashboard - My Chauffe',
        'user': request.user,
        'current_time': timezone.now(),
    })


def about(request):
    """About page"""
    return render(request, 'core/about.html', {
        'title': 'About - My Chauffe'
    })
