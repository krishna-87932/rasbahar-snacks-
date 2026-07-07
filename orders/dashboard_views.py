"""
Custom Admin Dashboard Views
Full CRUD operations for Orders, Menu, Categories, and Users.
All mutating operations return JSON for AJAX consumption.
"""
import json
import os
from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse
from django.db.models import Sum, Count, Q, Avg
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.utils.text import slugify
from datetime import timedelta
from .models import Order, OrderItem, Cart, CartItem
from menu.models import MenuItem, Category
from accounts.models import User


# ──────────────────────────────────────────────
# DASHBOARD OVERVIEW
# ──────────────────────────────────────────────

@staff_member_required
def admin_dashboard(request):
    """Main dashboard with statistics and charts."""
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    last_7_days = timezone.now() - timedelta(days=7)

    all_orders = Order.objects.all()
    today_orders = all_orders.filter(created_at__date=today)
    delivered_orders = all_orders.filter(status=Order.STATUS_DELIVERED)

    # Order stats
    order_stats = {
        'total': all_orders.count(),
        'pending': all_orders.filter(status=Order.STATUS_PENDING).count(),
        'confirmed': all_orders.filter(status=Order.STATUS_CONFIRMED).count(),
        'preparing': all_orders.filter(status=Order.STATUS_PREPARING).count(),
        'ready': all_orders.filter(status=Order.STATUS_READY).count(),
        'out_for_delivery': all_orders.filter(status=Order.STATUS_OUT_FOR_DELIVERY).count(),
        'delivered': delivered_orders.count(),
        'cancelled': all_orders.filter(status=Order.STATUS_CANCELLED).count(),
        'today': today_orders.count(),
    }

    # Revenue stats
    total_revenue = delivered_orders.aggregate(s=Sum('total'))['s'] or 0
    today_revenue = today_orders.filter(status=Order.STATUS_DELIVERED).aggregate(s=Sum('total'))['s'] or 0
    week_revenue = all_orders.filter(created_at__gte=last_7_days, status=Order.STATUS_DELIVERED).aggregate(s=Sum('total'))['s'] or 0
    month_revenue = all_orders.filter(created_at__date__gte=this_month_start, status=Order.STATUS_DELIVERED).aggregate(s=Sum('total'))['s'] or 0
    avg_order = delivered_orders.aggregate(a=Avg('total'))['a'] or 0

    revenue_stats = {
        'total': f"{total_revenue:,.0f}",
        'today': f"{today_revenue:,.0f}",
        'this_week': f"{week_revenue:,.0f}",
        'this_month': f"{month_revenue:,.0f}",
        'avg_order': f"{avg_order:,.0f}",
    }

    # Menu stats
    menu_stats = {
        'total_items': MenuItem.objects.count(),
        'available': MenuItem.objects.filter(is_available=True).count(),
        'unavailable': MenuItem.objects.filter(is_available=False).count(),
        'featured': MenuItem.objects.filter(is_featured=True).count(),
        'categories': Category.objects.count(),
    }

    # User stats
    user_stats = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'new_today': User.objects.filter(date_joined__date=today).count(),
        'new_this_month': User.objects.filter(date_joined__date__gte=this_month_start).count(),
    }

    # Recent orders
    recent_orders = all_orders.select_related('user').order_by('-created_at')[:10]

    # Top selling items
    top_items = MenuItem.objects.filter(
        orderitem__order__status=Order.STATUS_DELIVERED
    ).annotate(
        sold_count=Count('orderitem')
    ).order_by('-sold_count')[:5]

    # Daily revenue for last 7 days
    last_7_start = today - timedelta(days=6)
    daily_rev_qs = Order.objects.filter(
        created_at__date__gte=last_7_start, status=Order.STATUS_DELIVERED
    ).annotate(day=TruncDate('created_at')).values('day').annotate(total=Sum('total')).order_by('day')
    rev_dict = {r['day']: float(r['total']) for r in daily_rev_qs}

    daily_orders_qs = Order.objects.filter(
        created_at__date__gte=last_7_start
    ).annotate(day=TruncDate('created_at')).values('day').annotate(count=Count('id')).order_by('day')
    ord_dict = {r['day']: r['count'] for r in daily_orders_qs}

    daily_revenue = []
    daily_orders = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        daily_revenue.append({'date': d.strftime('%a'), 'value': rev_dict.get(d, 0)})
        daily_orders.append({'date': d.strftime('%a'), 'count': ord_dict.get(d, 0)})

    context = {
        'order_stats': order_stats,
        'revenue_stats': revenue_stats,
        'menu_stats': menu_stats,
        'user_stats': user_stats,
        'recent_orders': recent_orders,
        'top_items': top_items,
        'daily_revenue': daily_revenue,
        'daily_orders': daily_orders,
        'today': today,
        'ORDER_STATUS_CHOICES': Order.STATUS_CHOICES,
        'page': 'dashboard',
    }
    return render(request, 'admin_dashboard/dashboard.html', context)


# ──────────────────────────────────────────────
# ORDERS
# ──────────────────────────────────────────────

@staff_member_required
def orders_dashboard(request):
    """Orders management page."""
    orders = Order.objects.select_related('user').prefetch_related('order_items').order_by('-created_at')

    status_filter = request.GET.get('status', '')
    search = request.GET.get('q', '')

    if status_filter:
        orders = orders.filter(status=status_filter)
    if search:
        orders = orders.filter(
            Q(order_id__icontains=search) |
            Q(user__name__icontains=search) |
            Q(user__phone_number__icontains=search)
        )

    stats = {
        'total': Order.objects.count(),
        'pending': Order.objects.filter(status=Order.STATUS_PENDING).count(),
        'preparing': Order.objects.filter(status=Order.STATUS_PREPARING).count(),
        'ready': Order.objects.filter(status=Order.STATUS_READY).count(),
        'out_for_delivery': Order.objects.filter(status=Order.STATUS_OUT_FOR_DELIVERY).count(),
        'delivered': Order.objects.filter(status=Order.STATUS_DELIVERED).count(),
        'cancelled': Order.objects.filter(status=Order.STATUS_CANCELLED).count(),
    }

    context = {
        'orders': orders[:100],
        'stats': stats,
        'status_filter': status_filter,
        'search': search,
        'ORDER_STATUS_CHOICES': Order.STATUS_CHOICES,
        'page': 'orders',
    }
    return render(request, 'admin_dashboard/orders.html', context)


@staff_member_required
@require_GET
def order_detail_api(request, order_id):
    """Return order details as JSON for modal popup."""
    order = get_object_or_404(Order.objects.select_related('user'), pk=order_id)
    items = []
    for oi in order.order_items.all():
        items.append({
            'name': oi.item_name,
            'price': str(oi.item_price),
            'quantity': oi.quantity,
            'subtotal': str(oi.subtotal),
        })

    data = {
        'id': order.id,
        'order_id': str(order.order_id),
        'short_id': order.short_id,
        'customer_name': order.user.name,
        'customer_phone': order.user.phone_number,
        'customer_email': order.user.email,
        'status': order.status,
        'status_display': order.get_status_display(),
        'payment_method': order.get_payment_method_display(),
        'payment_status': order.payment_status,
        'delivery_address': order.delivery_address,
        'delivery_notes': order.delivery_notes,
        'subtotal': str(order.subtotal),
        'delivery_charge': str(order.delivery_charge),
        'discount': str(order.discount),
        'total': str(order.total),
        'created_at': order.created_at.strftime('%d %b %Y, %I:%M %p'),
        'items': items,
    }
    return JsonResponse(data)


@staff_member_required
@require_POST
def update_order_status_api(request, order_id):
    """Update order status via AJAX."""
    order = get_object_or_404(Order, pk=order_id)
    new_status = request.POST.get('status', '').strip()

    if new_status not in dict(Order.STATUS_CHOICES):
        return JsonResponse({'success': False, 'error': 'Invalid status.'}, status=400)

    old_status = order.get_status_display()
    order.status = new_status
    order.save()

    return JsonResponse({
        'success': True,
        'new_status': new_status,
        'new_status_display': order.get_status_display(),
        'message': f'Order #{order.short_id} updated to {order.get_status_display()}',
    })


# ──────────────────────────────────────────────
# MENU ITEMS
# ──────────────────────────────────────────────

@staff_member_required
def menu_dashboard(request):
    """Menu items management page."""
    items = MenuItem.objects.select_related('category').order_by('-created_at')
    categories = Category.objects.annotate(item_count=Count('items')).order_by('sort_order', 'name')

    cat_filter = request.GET.get('category', '')
    search = request.GET.get('q', '')

    if cat_filter:
        items = items.filter(category_id=cat_filter)
    if search:
        items = items.filter(Q(name__icontains=search) | Q(description__icontains=search))

    stats = {
        'total': MenuItem.objects.count(),
        'available': MenuItem.objects.filter(is_available=True).count(),
        'unavailable': MenuItem.objects.filter(is_available=False).count(),
        'featured': MenuItem.objects.filter(is_featured=True).count(),
    }

    context = {
        'items': items,
        'categories': categories,
        'cat_filter': cat_filter,
        'search': search,
        'stats': stats,
        'page': 'menu',
    }
    return render(request, 'admin_dashboard/menu.html', context)


@staff_member_required
@require_POST
def toggle_menu_item(request, item_id):
    """Toggle availability or featured status via AJAX."""
    item = get_object_or_404(MenuItem, pk=item_id)
    field = request.POST.get('field', 'is_available')

    if field == 'is_available':
        item.is_available = not item.is_available
        item.save(update_fields=['is_available'])
        return JsonResponse({'success': True, 'value': item.is_available, 'field': field})
    elif field == 'is_featured':
        item.is_featured = not item.is_featured
        item.save(update_fields=['is_featured'])
        return JsonResponse({'success': True, 'value': item.is_featured, 'field': field})
    return JsonResponse({'success': False, 'error': 'Invalid field.'}, status=400)


@staff_member_required
@require_POST
def add_menu_item(request):
    """Add a new menu item via AJAX form."""
    try:
        name = request.POST.get('name', '').strip()
        category_id = request.POST.get('category', '')
        price = request.POST.get('price', '')
        description = request.POST.get('description', '').strip()
        is_veg = request.POST.get('is_veg') == 'on'
        is_spicy = request.POST.get('is_spicy') == 'on'
        is_available = request.POST.get('is_available') == 'on'
        is_featured = request.POST.get('is_featured') == 'on'
        calories = request.POST.get('calories', '') or None
        prep_time = request.POST.get('prep_time_minutes', '') or 10
        image = request.FILES.get('image')

        if not name or not category_id or not price:
            return JsonResponse({'success': False, 'error': 'Name, category and price are required.'}, status=400)

        category = get_object_or_404(Category, pk=category_id)

        item = MenuItem.objects.create(
            name=name,
            slug=slugify(name),
            category=category,
            price=price,
            description=description,
            is_veg=is_veg,
            is_spicy=is_spicy,
            is_available=is_available,
            is_featured=is_featured,
            calories=int(calories) if calories else None,
            prep_time_minutes=int(prep_time),
            image=image,
        )
        return JsonResponse({
            'success': True,
            'message': f'"{item.name}" added successfully!',
            'item_id': item.id,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@staff_member_required
@require_POST
def edit_menu_item(request, item_id):
    """Edit a menu item via AJAX form."""
    item = get_object_or_404(MenuItem, pk=item_id)
    try:
        item.name = request.POST.get('name', item.name).strip()
        category_id = request.POST.get('category', item.category_id)
        item.category = get_object_or_404(Category, pk=category_id)
        item.price = request.POST.get('price', item.price)
        item.description = request.POST.get('description', item.description).strip()
        item.is_veg = request.POST.get('is_veg') == 'on'
        item.is_spicy = request.POST.get('is_spicy') == 'on'
        item.is_available = request.POST.get('is_available') == 'on'
        item.is_featured = request.POST.get('is_featured') == 'on'
        cal = request.POST.get('calories', '')
        item.calories = int(cal) if cal else None
        pt = request.POST.get('prep_time_minutes', '')
        item.prep_time_minutes = int(pt) if pt else 10

        image = request.FILES.get('image')
        if image:
            item.image = image

        item.save()
        return JsonResponse({
            'success': True,
            'message': f'"{item.name}" updated successfully!',
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@staff_member_required
@require_POST
def delete_menu_item(request, item_id):
    """Delete a menu item via AJAX."""
    item = get_object_or_404(MenuItem, pk=item_id)
    name = item.name
    item.delete()
    return JsonResponse({'success': True, 'message': f'"{name}" deleted successfully!'})


@staff_member_required
@require_GET
def menu_item_detail_api(request, item_id):
    """Return menu item details as JSON for edit modal."""
    item = get_object_or_404(MenuItem.objects.select_related('category'), pk=item_id)
    data = {
        'id': item.id,
        'name': item.name,
        'category_id': item.category_id,
        'category_name': item.category.name,
        'price': str(item.price),
        'description': item.description,
        'is_veg': item.is_veg,
        'is_spicy': item.is_spicy,
        'is_available': item.is_available,
        'is_featured': item.is_featured,
        'calories': item.calories,
        'prep_time_minutes': item.prep_time_minutes,
        'image_url': item.image.url if item.image else '',
    }
    return JsonResponse(data)


# ──────────────────────────────────────────────
# CATEGORIES
# ──────────────────────────────────────────────

@staff_member_required
def categories_dashboard(request):
    """Categories management page."""
    categories = Category.objects.annotate(item_count=Count('items')).order_by('sort_order', 'name')
    context = {'categories': categories, 'page': 'categories'}
    return render(request, 'admin_dashboard/categories.html', context)


@staff_member_required
@require_POST
def add_category(request):
    """Add a new category via AJAX."""
    try:
        name = request.POST.get('name', '').strip()
        icon = request.POST.get('icon', '').strip()
        description = request.POST.get('description', '').strip()
        sort_order = request.POST.get('sort_order', 0) or 0
        is_active = request.POST.get('is_active') == 'on'
        image = request.FILES.get('image')

        if not name:
            return JsonResponse({'success': False, 'error': 'Category name is required.'}, status=400)

        cat = Category.objects.create(
            name=name,
            slug=slugify(name),
            icon=icon,
            description=description,
            sort_order=int(sort_order),
            is_active=is_active,
            image=image,
        )
        return JsonResponse({'success': True, 'message': f'Category "{cat.name}" created!', 'id': cat.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@staff_member_required
@require_POST
def edit_category(request, cat_id):
    """Edit a category via AJAX."""
    cat = get_object_or_404(Category, pk=cat_id)
    try:
        cat.name = request.POST.get('name', cat.name).strip()
        cat.icon = request.POST.get('icon', cat.icon).strip()
        cat.description = request.POST.get('description', cat.description).strip()
        so = request.POST.get('sort_order', cat.sort_order)
        cat.sort_order = int(so) if so else 0
        cat.is_active = request.POST.get('is_active') == 'on'
        image = request.FILES.get('image')
        if image:
            cat.image = image
        cat.save()
        return JsonResponse({'success': True, 'message': f'Category "{cat.name}" updated!'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@staff_member_required
@require_POST
def delete_category(request, cat_id):
    """Delete a category via AJAX."""
    cat = get_object_or_404(Category, pk=cat_id)
    name = cat.name
    if cat.items.exists():
        return JsonResponse({
            'success': False,
            'error': f'Cannot delete "{name}" — it has {cat.items.count()} menu items. Move or delete them first.'
        }, status=400)
    cat.delete()
    return JsonResponse({'success': True, 'message': f'Category "{name}" deleted!'})


@staff_member_required
@require_GET
def category_detail_api(request, cat_id):
    """Return category details as JSON for edit modal."""
    cat = get_object_or_404(Category, pk=cat_id)
    data = {
        'id': cat.id,
        'name': cat.name,
        'slug': cat.slug,
        'icon': cat.icon,
        'description': cat.description,
        'sort_order': cat.sort_order,
        'is_active': cat.is_active,
        'image_url': cat.image.url if cat.image else '',
    }
    return JsonResponse(data)


# ──────────────────────────────────────────────
# USERS
# ──────────────────────────────────────────────

@staff_member_required
def users_dashboard(request):
    """Users management page."""
    users = User.objects.annotate(order_count=Count('orders')).order_by('-date_joined')

    search = request.GET.get('q', '')
    role_filter = request.GET.get('role', '')

    if search:
        users = users.filter(
            Q(name__icontains=search) |
            Q(phone_number__icontains=search) |
            Q(email__icontains=search)
        )
    if role_filter == 'staff':
        users = users.filter(is_staff=True)
    elif role_filter == 'active':
        users = users.filter(is_active=True, is_staff=False)
    elif role_filter == 'inactive':
        users = users.filter(is_active=False)

    stats = {
        'total': User.objects.count(),
        'active': User.objects.filter(is_active=True).count(),
        'inactive': User.objects.filter(is_active=False).count(),
        'staff': User.objects.filter(is_staff=True).count(),
    }

    context = {
        'users': users[:100],
        'stats': stats,
        'search': search,
        'role_filter': role_filter,
        'page': 'users',
    }
    return render(request, 'admin_dashboard/users.html', context)


@staff_member_required
@require_POST
def toggle_user_status(request, user_id):
    """Toggle user active or staff status via AJAX."""
    user = get_object_or_404(User, pk=user_id)
    field = request.POST.get('field', 'is_active')

    if field == 'is_active':
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
        return JsonResponse({'success': True, 'value': user.is_active, 'field': field})
    elif field == 'is_staff':
        user.is_staff = not user.is_staff
        user.save(update_fields=['is_staff'])
        return JsonResponse({'success': True, 'value': user.is_staff, 'field': field})
    return JsonResponse({'success': False, 'error': 'Invalid field.'}, status=400)


@staff_member_required
@require_GET
def user_detail_api(request, user_id):
    """Return user details as JSON for modal."""
    user = get_object_or_404(User, pk=user_id)
    orders = user.orders.order_by('-created_at')[:10]
    total_spent = user.orders.filter(status=Order.STATUS_DELIVERED).aggregate(s=Sum('total'))['s'] or 0

    data = {
        'id': user.id,
        'name': user.name,
        'phone_number': user.phone_number,
        'email': user.email,
        'address': user.address,
        'is_active': user.is_active,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'date_joined': user.date_joined.strftime('%d %b %Y, %I:%M %p'),
        'last_login': user.last_login.strftime('%d %b %Y, %I:%M %p') if user.last_login else 'Never',
        'profile_picture_url': user.profile_picture.url if user.profile_picture else '',
        'total_orders': user.orders.count(),
        'total_spent': str(total_spent),
        'recent_orders': [
            {
                'short_id': o.short_id,
                'status': o.get_status_display(),
                'total': str(o.total),
                'date': o.created_at.strftime('%d %b %Y'),
            }
            for o in orders
        ],
    }
    return JsonResponse(data)
