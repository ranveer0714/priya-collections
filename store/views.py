from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CheckoutForm
from .models import Category, Order, OrderItem, Product


HERO_SLIDES = [
    {
        'title': 'Exclusive Gold Collection',
        'subtitle': 'Discover handcrafted gold jewellery for every occasion.',
        'image': 'https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?auto=format&fit=crop&w=1600&q=80',
    },
    {
        'title': 'Diamond & Gemstone Elegance',
        'subtitle': 'Premium designs made to shine with your moments.',
        'image': 'https://images.unsplash.com/photo-1605100804763-247f67b3557e?auto=format&fit=crop&w=1600&q=80',
    },
    {
        'title': 'Pearl Classics',
        'subtitle': 'Soft, timeless jewellery with a luxury finish.',
        'image': 'https://images.unsplash.com/photo-1506630448388-4e683c67ddb0?auto=format&fit=crop&w=1600&q=80',
    },
]


def _get_cart(request):
    cart = request.session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}
    return cart


def _save_cart(request, cart):
    request.session['cart'] = cart
    request.session.modified = True


def _clean_cart(request):
    cart = _get_cart(request)
    product_ids = list(cart.keys())
    products = Product.objects.filter(id__in=product_ids)
    product_map = {str(product.id): product for product in products}
    cleaned = {}
    items = []
    total = Decimal('0.00')

    for product_id, quantity in cart.items():
        product = product_map.get(str(product_id))
        if not product:
            continue
        quantity = max(int(quantity), 1)
        subtotal = product.current_price * quantity
        cleaned[str(product.id)] = quantity
        total += subtotal
        items.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})

    if cleaned != cart:
        _save_cart(request, cleaned)

    return items, total


def _get_wishlist(request):
    wishlist_ids = request.session.get('wishlist', [])
    if not isinstance(wishlist_ids, list):
        wishlist_ids = []

    products = Product.objects.filter(id__in=wishlist_ids)
    existing_ids = [product.id for product in products]
    if sorted(existing_ids) != sorted(wishlist_ids):
        request.session['wishlist'] = existing_ids
        request.session.modified = True
    return products


def home(request):
    products = Product.objects.select_related('category')[:12]
    categories = Category.objects.all()
    return render(request, 'store/home.html', {
        'hero_slides': HERO_SLIDES,
        'products': products,
        'categories': categories,
    })


def products(request):
    product_list = Product.objects.select_related('category')
    categories = Category.objects.all()
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()

    if query:
        product_list = product_list.filter(Q(title__icontains=query) | Q(category__name__icontains=query))
    if category_id:
        product_list = product_list.filter(category_id=category_id)

    paginator = Paginator(product_list, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'store/products.html', {
        'page_obj': page_obj,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
    })


def category_list(request):
    categories = Category.objects.all()
    return render(request, 'store/category_list.html', {'categories': categories})


def category_products(request, category_id, slug):
    category = get_object_or_404(Category, pk=category_id)
    product_list = Product.objects.filter(category=category)
    paginator = Paginator(product_list, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'store/category_products.html', {
        'category': category,
        'page_obj': page_obj,
    })


def product_detail(request, pk):
    product = get_object_or_404(Product.objects.select_related('category'), pk=pk)
    related_products = Product.objects.filter(category=product.category).exclude(pk=product.pk)[:4]
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related_products': related_products,
    })


def cart(request):
    items, total = _clean_cart(request)
    return render(request, 'store/cart.html', {'items': items, 'total': total})


def checkout(request):
    items, total = _clean_cart(request)
    if not items:
        messages.info(request, 'Your cart is empty. Add a product before checkout.')
        return redirect('cart')

    initial = {}
    if request.user.is_authenticated:
        initial = {
            'customer_name': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
        }
    form = CheckoutForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            order = form.save(commit=False)
            order.user = request.user if request.user.is_authenticated else None
            order.total_amount = total
            order.save()
            OrderItem.objects.bulk_create([
                OrderItem(
                    order=order,
                    product=item['product'],
                    product_title=item['product'].title,
                    quantity=item['quantity'],
                    unit_price=item['product'].current_price,
                )
                for item in items
            ])

        _save_cart(request, {})
        messages.success(request, f'Order #{order.pk} placed successfully.')
        return redirect('order_confirmation', token=order.confirmation_token)

    return render(request, 'store/checkout.html', {
        'form': form,
        'items': items,
        'total': total,
    })


def order_confirmation(request, token):
    order = get_object_or_404(
        Order.objects.prefetch_related('items'),
        confirmation_token=token,
    )
    return render(request, 'store/order_confirmation.html', {'order': order})


def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    cart = _get_cart(request)
    product_id = str(product.pk)
    cart[product_id] = int(cart.get(product_id, 0)) + 1
    _save_cart(request, cart)
    messages.success(request, f'{product.title} added to cart.')
    return redirect(request.META.get('HTTP_REFERER', 'cart'))


def decrease_cart(request, pk):
    cart = _get_cart(request)
    product_id = str(pk)
    if product_id in cart:
        cart[product_id] = int(cart[product_id]) - 1
        if cart[product_id] <= 0:
            cart.pop(product_id)
    _save_cart(request, cart)
    return redirect('cart')


def remove_from_cart(request, pk):
    cart = _get_cart(request)
    cart.pop(str(pk), None)
    _save_cart(request, cart)
    messages.info(request, 'Product removed from cart.')
    return redirect('cart')


def wishlist(request):
    products = _get_wishlist(request)
    return render(request, 'store/wishlist.html', {'products': products})


def add_to_wishlist(request, pk):
    product = get_object_or_404(Product, pk=pk)
    wishlist_ids = request.session.get('wishlist', [])
    if product.pk not in wishlist_ids:
        wishlist_ids.append(product.pk)
        request.session['wishlist'] = wishlist_ids
        request.session.modified = True
        messages.success(request, f'{product.title} added to wishlist.')
    return redirect(request.META.get('HTTP_REFERER', 'wishlist'))


def remove_from_wishlist(request, pk):
    wishlist_ids = request.session.get('wishlist', [])
    if pk in wishlist_ids:
        wishlist_ids.remove(pk)
        request.session['wishlist'] = wishlist_ids
        request.session.modified = True
    messages.info(request, 'Product removed from wishlist.')
    return redirect('wishlist')


def about(request):
    return render(request, 'store/about.html')


def contact(request):
    return render(request, 'store/contact.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password'],
        )
        if user is not None:
            login(request, user)
            messages.success(request, 'Welcome back.')
            return redirect(request.GET.get('next') or 'home')

    return render(request, 'store/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = UserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Your account has been created.')
        return redirect('home')

    return render(request, 'store/register.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')
