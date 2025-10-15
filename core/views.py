from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Product, Order, License, CHAUFFEcoinTransaction, UserProfile
from .decorators import profile_required, profile_required_ajax
from decimal import Decimal
import json
import stripe
from django.conf import settings


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
    order_id = request.GET.get('order_id')
    order = None
    purchase_context = None
    
    if order_id:
        try:
            order = Order.objects.select_related('product', 'user').get(
                id=order_id, user=request.user, status='completed'
            )
            
            # Calculate license count from transaction
            calculated_license_count = int(order.total_amount / order.product.price)
            
            # Validate that calculated count matches requested quantity
            if calculated_license_count != order.quantity:
                messages.error(request, f'Transaction validation error: Expected {order.quantity} licenses but payment is for {calculated_license_count} licenses.')
                return redirect('core:store')
            
            # Get license associated with this order
            license_obj = getattr(order, 'license', None)
            
            purchase_context = {
                'order': order,
                'license': license_obj,
                'product': order.product,
                'license_count': calculated_license_count,
                'total_amount': order.total_amount,
                'chauffecoins_earned': order.product.chauffecoins_included * order.quantity,
                'is_post_purchase': True
            }
        except Order.DoesNotExist:
            messages.error(request, 'Order not found or access denied.')
    
    # Get or create user profile to access UUID
    user_profile, created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'chauffecoins_balance': 0}
    )
    
    return render(request, 'core/controller_generator.html', {
        'title': 'Controller Name Generator - My Chauffe',
        'purchase_context': purchase_context,
        'order': order,
        'user_first_name': request.user.first_name or '',
        'user_last_name': request.user.last_name or '',
        'user_uuid': user_profile.get_uuid_string()
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


# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


def get_cart_items(request):
    """Helper function to get cart items from session"""
    cart = request.session.get('cart', {})
    cart_items = []
    cart_total = Decimal('0.00')
    total_chauffecoins = 0
    
    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=product_id, is_active=True)
            total_price = product.price * quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total_price': total_price
            })
            cart_total += total_price
            total_chauffecoins += product.chauffecoins_included * quantity
        except Product.DoesNotExist:
            # Remove invalid products from cart
            del cart[product_id]
            request.session['cart'] = cart
    
    return cart_items, cart_total, total_chauffecoins


def get_cart_items_count(request):
    """Helper function to get total items count in cart"""
    cart = request.session.get('cart', {})
    return sum(cart.values())


@profile_required
def store(request):
    """Store page displaying available products"""
    products = Product.objects.filter(is_active=True).order_by('-created_at')
    cart_items_count = get_cart_items_count(request)
    
    return render(request, 'core/store.html', {
        'title': 'CHAUFFE Store',
        'products': products,
        'cart_items_count': cart_items_count,
    })


@profile_required
def cart(request):
    """Shopping cart page"""
    cart_items, cart_total, total_chauffecoins = get_cart_items(request)
    
    return render(request, 'core/cart.html', {
        'title': 'Shopping Cart - My Chauffe',
        'cart_items': cart_items,
        'cart_total': cart_total,
        'total_chauffecoins': total_chauffecoins,
    })


@profile_required_ajax
@require_POST
def add_to_cart(request):
    """Add product to cart via AJAX"""
    print(f"DEBUG: add_to_cart called with method={request.method}")
    print(f"DEBUG: Content-Type={request.content_type}")
    print(f"DEBUG: Raw body={request.body[:200]}")
    
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        print(f"DEBUG: Parsed data - product_id={product_id}, quantity={quantity}")
        
        # Validate quantity
        if not isinstance(quantity, int) or quantity < 1:
            return JsonResponse({
                'success': False,
                'error': 'Quantity must be at least 1'
            })
        
        if quantity > 9999:
            return JsonResponse({
                'success': False,
                'error': 'Maximum quantity is 9999'
            })
        
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        cart = request.session.get('cart', {})
        current_qty = cart.get(str(product_id), 0)
        new_total = current_qty + quantity
        
        # Check if adding this quantity would exceed the limit
        if new_total > 9999:
            return JsonResponse({
                'success': False,
                'error': f'Cannot add {quantity}. Maximum total quantity per item is 9999 (currently have {current_qty})'
            })
        
        cart[str(product_id)] = new_total
        request.session['cart'] = cart
        
        cart_items_count = get_cart_items_count(request)
        
        return JsonResponse({
            'success': True,
            'message': 'Product added to cart',
            'cart_items_count': cart_items_count
        })
        
    except json.JSONDecodeError as e:
        print(f"DEBUG: JSON decode error: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Invalid JSON data: {str(e)}'
        })
    except Product.DoesNotExist:
        print(f"DEBUG: Product not found: {product_id}")
        return JsonResponse({
            'success': False,
            'error': 'Product not found'
        })
    except Exception as e:
        print(f"DEBUG: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@profile_required_ajax
@require_POST
def update_cart(request):
    """Update cart item quantity via AJAX"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        
        # Validate quantity type and range
        if not isinstance(quantity, int) or quantity < 1:
            return JsonResponse({
                'success': False,
                'error': 'Quantity must be at least 1'
            })
        
        if quantity > 9999:
            return JsonResponse({
                'success': False,
                'error': 'Maximum quantity is 9999'
            })
        
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        cart = request.session.get('cart', {})
        cart[str(product_id)] = quantity
        request.session['cart'] = cart
        
        return JsonResponse({
            'success': True,
            'message': 'Cart updated'
        })
        
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Product not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@profile_required_ajax
@require_POST
def remove_from_cart(request):
    """Remove item from cart via AJAX"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        cart = request.session.get('cart', {})
        if str(product_id) in cart:
            del cart[str(product_id)]
            request.session['cart'] = cart
        
        return JsonResponse({
            'success': True,
            'message': 'Item removed from cart'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@profile_required
def checkout(request):
    """Checkout page for processing payments"""
    cart_items, cart_total, total_chauffecoins = get_cart_items(request)
    
    if not cart_items:
        messages.error(request, 'Your cart is empty.')
        return redirect('core:store')
    
    return render(request, 'core/checkout.html', {
        'title': 'Checkout - My Chauffe',
        'cart_items': cart_items,
        'cart_total': cart_total,
        'total_chauffecoins': total_chauffecoins,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    })


@profile_required_ajax
@require_POST
def create_payment_intent(request):
    """Create Stripe payment intent for checkout"""
    try:
        data = json.loads(request.body)
        payment_method_id = data.get('payment_method_id')
        cardholder_name = data.get('cardholder_name')
        
        if not payment_method_id or not cardholder_name:
            return JsonResponse({
                'success': False,
                'error': 'Missing required payment information'
            })
        
        cart_items, cart_total, total_chauffecoins = get_cart_items(request)
        
        if not cart_items:
            return JsonResponse({
                'success': False,
                'error': 'Your cart is empty'
            })
        
        # Create orders for each cart item
        orders = []
        for item in cart_items:
            order = Order.objects.create(
                user=request.user,
                product=item['product'],
                quantity=item['quantity'],
                total_amount=item['total_price'],
                status='pending'
            )
            orders.append(order)
        
        # Calculate total amount in cents for Stripe
        total_cents = int(cart_total * 100)
        
        # Create payment intent for immediate confirmation
        payment_intent = stripe.PaymentIntent.create(
            amount=total_cents,
            currency=settings.STRIPE_CURRENCY,
            metadata={
                'user_id': request.user.id,
                'order_ids': ','.join([str(order.id) for order in orders]),
                'cardholder_name': cardholder_name
            }
        )
        
        # Confirm the payment intent with the payment method
        payment_intent = stripe.PaymentIntent.confirm(
            payment_intent.id,
            payment_method=payment_method_id,
            return_url=request.build_absolute_uri('/controller-generator/')
        )
        
        # Update orders with payment intent ID
        for order in orders:
            order.stripe_payment_intent_id = payment_intent.id
            order.save()
        
        if payment_intent.status == 'requires_action':
            return JsonResponse({
                'success': False,
                'error': 'Payment requires additional authentication',
                'requires_action': True,
                'payment_intent': {
                    'id': payment_intent.id,
                    'client_secret': payment_intent.client_secret
                }
            })
        elif payment_intent.status == 'succeeded':
            # Payment succeeded immediately
            success_result = handle_successful_payment(request, orders, payment_intent, total_chauffecoins)
            return JsonResponse({
                'success': True,
                'order_id': orders[0].id if orders else None,
                'client_secret': payment_intent.client_secret
            })
        else:
            # Mark orders as failed
            for order in orders:
                order.status = 'failed'
                order.save()
            
            return JsonResponse({
                'success': False,
                'error': f'Payment failed with status: {payment_intent.status}'
            })
        
    except stripe.error.CardError as e:
        return JsonResponse({
            'success': False,
            'error': e.user_message or 'Your card was declined.'
        })
    except stripe.error.StripeError as e:
        return JsonResponse({
            'success': False,
            'error': 'Payment processing error. Please try again.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def handle_successful_payment(request, orders, payment_intent, total_chauffecoins):
    """Handle successful payment processing"""
    try:
        # Update order status
        for order in orders:
            order.status = 'completed'
            order.save()
            
            # Create licenses based on order quantity
            for i in range(order.quantity):
                license_obj = License.objects.create(
                    user=request.user,
                    order=order
                )
        
        # Get or create user profile
        user_profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'chauffecoins_balance': 0}
        )
        
        # Add CHAUFFEcoins to user balance
        if total_chauffecoins > 0:
            user_profile.update_balance(
                amount=total_chauffecoins,
                transaction_type='earned',
                description=f'CHAUFFEcoins from license purchase - Orders: {", ".join([str(o.id) for o in orders])}',
                order=orders[0] if orders else None
            )
        
        # Update license count - account for quantity in each order
        total_licenses = sum(order.quantity for order in orders)
        user_profile.total_licenses_purchased += total_licenses
        user_profile.save()
        
        # Clear cart
        request.session['cart'] = {}
        
        return True
        
    except Exception as e:
        # If anything fails, mark orders as failed
        for order in orders:
            order.status = 'failed'
            order.save()
        raise e


@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhook events"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    
    if not endpoint_secret:
        return HttpResponse('Webhook secret not configured', status=400)
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        # Invalid payload
        return HttpResponse('Invalid payload', status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return HttpResponse('Invalid signature', status=400)
    
    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        handle_payment_intent_succeeded(payment_intent)
    
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        handle_payment_intent_failed(payment_intent)
    
    else:
        print(f'Unhandled event type: {event["type"]}')
    
    return HttpResponse('Success', status=200)


def handle_payment_intent_succeeded(payment_intent):
    """Handle successful payment intent from webhook"""
    try:
        payment_intent_id = payment_intent['id']
        user_id = payment_intent['metadata'].get('user_id')
        order_ids = payment_intent['metadata'].get('order_ids', '').split(',')
        
        if not user_id or not order_ids:
            print(f'Missing metadata in payment intent {payment_intent_id}')
            return
        
        user = User.objects.get(id=user_id)
        orders = Order.objects.filter(
            id__in=[oid.strip() for oid in order_ids if oid.strip()],
            stripe_payment_intent_id=payment_intent_id
        )
        
        total_chauffecoins = 0
        
        for order in orders:
            if order.status != 'completed':
                order.status = 'completed'
                order.save()
                
                # Create licenses if they don't exist (based on order quantity)
                existing_licenses = License.objects.filter(order=order).count()
                licenses_needed = order.quantity - existing_licenses
                
                for i in range(licenses_needed):
                    License.objects.create(
                        user=user,
                        order=order
                    )
                
                total_chauffecoins += order.product.chauffecoins_included * order.quantity
        
        # Update user profile
        if total_chauffecoins > 0:
            user_profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'chauffecoins_balance': 0}
            )
            
            user_profile.update_balance(
                amount=total_chauffecoins,
                transaction_type='earned',
                description=f'CHAUFFEcoins from webhook - Payment Intent: {payment_intent_id}',
                order=orders.first() if orders else None
            )
            
            total_licenses = sum(order.quantity for order in orders)
            user_profile.total_licenses_purchased += total_licenses
            user_profile.save()
        
        print(f'Successfully processed payment intent {payment_intent_id} for user {user_id}')
        
    except Exception as e:
        print(f'Error processing successful payment intent {payment_intent["id"]}: {e}')


def handle_payment_intent_failed(payment_intent):
    """Handle failed payment intent from webhook"""
    try:
        payment_intent_id = payment_intent['id']
        orders = Order.objects.filter(stripe_payment_intent_id=payment_intent_id)
        
        for order in orders:
            order.status = 'failed'
            order.save()
        
        print(f'Marked orders as failed for payment intent {payment_intent_id}')
        
    except Exception as e:
        print(f'Error processing failed payment intent {payment_intent["id"]}: {e}')


@login_required
def api_test(request):
    """API testing page for CloudManager integration"""
    return render(request, 'core/api_test.html', {
        'title': 'CloudManager API Test - My Chauffe'
    })
