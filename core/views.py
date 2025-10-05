from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


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


@login_required
def controller_generator(request):
    """Controller name generator page"""
    return render(request, 'core/controller_generator.html', {
        'title': 'Controller Name Generator - My Chauffe'
    })


@csrf_exempt
def health_check(request):
    """Health check endpoint for Fly.io"""
    return HttpResponse("OK", content_type="text/plain")


@csrf_exempt
def api_health_check(request):
    """API health check endpoint"""
    from django.http import JsonResponse
    return JsonResponse({"status": "ok", "message": "API is healthy"})
