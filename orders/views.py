from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from .models import Cart, CartItem, Order, OrderItem
from menu.models import MenuItem


def is_staff(user):
    return user.is_staff


def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


@login_required
def cart_view(request):
    cart = get_or_create_cart(request.user)
    return render(request, 'orders/cart.html', {'cart': cart})


@login_required
@require_POST
def add_to_cart(request, item_id):
    item = get_object_or_404(MenuItem, pk=item_id, is_available=True)
    cart = get_or_create_cart(request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, menu_item=item)
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'cart_count': cart.item_count})

    messages.success(request, f"Added {item.name} to cart!")
    return redirect('menu:menu')


@login_required
@require_POST
def update_cart(request, item_id):
    cart = get_or_create_cart(request.user)
    cart_item = get_object_or_404(CartItem, cart=cart, menu_item_id=item_id)
    action = request.POST.get('action')

    if action == 'increase':
        cart_item.quantity += 1
        cart_item.save()
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    elif action == 'remove':
        cart_item.delete()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_count': cart.item_count,
            'cart_total': str(cart.total),
        })
    return redirect('orders:cart')


@login_required
def checkout_view(request):
    cart = get_or_create_cart(request.user)
    if not cart.cart_items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('orders:cart')

    # Check if user has set their delivery location
    if not request.user.has_location:
        messages.warning(request, 'Please set your delivery location first.')
        return redirect('accounts:add_address')

    # Check if user is within delivery range
    if not request.user.is_within_delivery_range:
        distance = request.user.distance_from_restaurant_km
        messages.error(
            request,
            f'😔 Sorry! We currently don\'t deliver to your area. '
            f'You are {distance} KM away (we deliver within {settings.MAX_DELIVERY_RADIUS_KM} KM).'
        )
        return redirect('orders:cart')

    if request.method == 'POST':
        address = request.POST.get('delivery_address', '').strip()
        notes = request.POST.get('delivery_notes', '').strip()
        payment_method = request.POST.get('payment_method', Order.PAYMENT_COD)

        if not address:
            messages.error(request, 'Delivery address is required.')
            return redirect('orders:checkout')

        order = Order.objects.create(
            user=request.user,
            delivery_address=address,
            delivery_notes=notes,
            payment_method=payment_method,
            delivery_charge=30,
        )
        for ci in cart.cart_items.all():
            OrderItem.objects.create(
                order=order,
                menu_item=ci.menu_item,
                item_name=ci.menu_item.name,
                item_price=ci.menu_item.price,
                quantity=ci.quantity,
            )
        order.calculate_totals()
        cart.cart_items.all().delete()

        messages.success(request, f"Order #{order.short_id} placed successfully! 🎉")
        return redirect('orders:order_detail', order_id=order.order_id)

    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'user': request.user,
        'delivery_charge': 30,
    })


@login_required
def order_list_view(request):
    orders = request.user.orders.all()
    return render(request, 'orders/order_list.html', {'orders': orders})


@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})


@user_passes_test(is_staff)
@require_POST
def update_order_status(request, order_id):
    """Update order status (staff only)"""
    order = get_object_or_404(Order, order_id=order_id)
    new_status = request.POST.get('status', '').strip()
    
    if new_status not in dict(Order.STATUS_CHOICES):
        messages.error(request, 'Invalid status.')
        return redirect('admin:orders_order_change', order.id)
    
    old_status = order.status
    order.status = new_status
    order.save()
    
    messages.success(request, f"Order #{order.short_id} status updated from {old_status} to {new_status}")
    return redirect('admin:orders_order_change', order.id)
