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
    
    # eCommerce URLs
    path('store/', views.store, name='store'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('purchase-success/', views.purchase_success, name='purchase_success'),
    path('api/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('api/update-cart/', views.update_cart, name='update_cart'),
    path('api/remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('api/create-payment-intent/', views.create_payment_intent, name='create_payment_intent'),
    path('api/stripe-webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('api-test/', views.api_test, name='api_test'),
]
