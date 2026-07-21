from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from .models import Cart, CartItem, CartItemAddOn, Order, OrderItem, OrderItemAddOn
from menu.models import MenuItem, AddOn


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
        # Return add-on suggestions for this item
        addons = item.addons.filter(is_available=True)
        addon_data = []
        for a in addons:
            addon_data.append({
                'id': a.id,
                'name': a.name,
                'price': str(a.price),
                'is_veg': a.is_veg,
                'image_url': a.image.url if a.image else '',
            })
        return JsonResponse({
            'success': True,
            'cart_count': cart.item_count,
            'cart_item_id': cart_item.id,
            'item_name': item.name,
            'addons': addon_data,
        })

    messages.success(request, f"Added {item.name} to cart!")
    return redirect('menu:menu')


@login_required
@require_POST
def add_addon_to_cart(request, cart_item_id):
    """Add an add-on to a specific cart item via AJAX."""
    cart = get_or_create_cart(request.user)
    cart_item = get_object_or_404(CartItem, pk=cart_item_id, cart=cart)

    addon_id = request.POST.get('addon_id')
    if not addon_id:
        return JsonResponse({'success': False, 'error': 'No addon specified.'}, status=400)

    addon = get_object_or_404(AddOn, pk=addon_id, is_available=True)

    # Check that this addon is actually linked to the menu item
    if not addon.menu_items.filter(pk=cart_item.menu_item_id).exists():
        return JsonResponse({'success': False, 'error': 'This add-on is not available for this item.'}, status=400)

    cart_addon, created = CartItemAddOn.objects.get_or_create(
        cart_item=cart_item, addon=addon,
        defaults={'quantity': 1}
    )
    if not created:
        cart_addon.quantity += 1
        cart_addon.save()

    return JsonResponse({
        'success': True,
        'addon_name': addon.name,
        'cart_count': cart.item_count,
    })


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
            oi = OrderItem.objects.create(
                order=order,
                menu_item=ci.menu_item,
                item_name=ci.menu_item.name,
                item_price=ci.menu_item.price,
                quantity=ci.quantity,
            )
            # Copy add-ons from cart item to order item
            for ca in ci.cart_addons.all():
                OrderItemAddOn.objects.create(
                    order_item=oi,
                    addon_name=ca.addon.name,
                    addon_price=ca.addon.price,
                    quantity=ca.quantity,
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
