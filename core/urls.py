from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('about/', views.about, name='about'),
    path('controller-generator/', views.controller_generator, name='controller_generator'),
    path('health/', views.health_check, name='health_check'),
    path('api/health/', views.api_health_check, name='api_health_check'),
]
