from django.shortcuts import render, get_object_or_404
from .models import Category, MenuItem


def home_view(request):
    categories = Category.objects.filter(is_active=True)
    featured_items = MenuItem.objects.filter(is_featured=True, is_available=True)[:6]
    return render(request, 'menu/home.html', {
        'categories': categories,
        'featured_items': featured_items,
    })


def menu_view(request):
    categories = Category.objects.filter(is_active=True).prefetch_related('items')
    selected_category = request.GET.get('category')
    veg_only = request.GET.get('veg') == '1'

    items = MenuItem.objects.filter(is_available=True)
    if selected_category:
        items = items.filter(category__slug=selected_category)
    if veg_only:
        items = items.filter(is_veg=True)

    return render(request, 'menu/menu.html', {
        'categories': categories,
        'items': items,
        'selected_category': selected_category,
        'veg_only': veg_only,
    })


def item_detail_view(request, slug):
    item = get_object_or_404(MenuItem, slug=slug, is_available=True)
    related = MenuItem.objects.filter(
        category=item.category, is_available=True
    ).exclude(pk=item.pk)[:4]
    return render(request, 'menu/item_detail.html', {'item': item, 'related': related})
