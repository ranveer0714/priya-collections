from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from store.models import Category, Order, Product

from .decorators import admin_staff_required
from .forms import CategoryForm, ProductForm


def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('adminpanel:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            messages.success(request, 'Welcome to the dashboard.')
            return redirect(request.GET.get('next') or 'adminpanel:dashboard')
        messages.error(request, 'Only staff users can access the dashboard.')

    return render(request, 'adminpanel/login.html')


@admin_staff_required
def admin_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out from the dashboard.')
    return redirect('adminpanel:login')


@admin_staff_required
def dashboard(request):
    latest_products = Product.objects.select_related('category')[:5]
    return render(request, 'adminpanel/dashboard.html', {
        'total_products': Product.objects.count(),
        'total_categories': Category.objects.count(),
        'total_orders': Order.objects.count(),
        'total_users': User.objects.count(),
        'latest_products': latest_products,
    })


@admin_staff_required
def product_list(request):
    products = Product.objects.select_related('category')
    categories = Category.objects.all()
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()

    if query:
        products = products.filter(title__icontains=query)
    if category_id:
        products = products.filter(category_id=category_id)

    paginator = Paginator(products, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'adminpanel/product_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
    })


@admin_staff_required
def product_create(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added successfully.')
            return redirect('adminpanel:product_list')
        messages.error(request, 'Please fix the errors below.')
    return render(request, 'adminpanel/product_form.html', {'form': form, 'title': 'Add Product'})


@admin_staff_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully.')
            return redirect('adminpanel:product_list')
        messages.error(request, 'Please fix the errors below.')
    return render(request, 'adminpanel/product_form.html', {'form': form, 'title': 'Edit Product', 'product': product})


@admin_staff_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully.')
        return redirect('adminpanel:product_list')
    return render(request, 'adminpanel/product_confirm_delete.html', {'product': product})


@admin_staff_required
def category_list(request):
    categories = Category.objects.prefetch_related('products')
    return render(request, 'adminpanel/category_list.html', {'categories': categories})


@admin_staff_required
def category_create(request):
    form = CategoryForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added successfully.')
            return redirect('adminpanel:category_list')
        messages.error(request, 'Please fix the errors below.')
    return render(request, 'adminpanel/category_form.html', {'form': form, 'title': 'Add Category'})


@admin_staff_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=category)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully.')
            return redirect('adminpanel:category_list')
        messages.error(request, 'Please fix the errors below.')
    return render(request, 'adminpanel/category_form.html', {'form': form, 'title': 'Edit Category'})


@admin_staff_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if category.products.exists():
        messages.error(request, 'This category has products. Move or delete those products first.')
        return redirect('adminpanel:category_list')
    category.delete()
    messages.success(request, 'Category deleted successfully.')
    return redirect('adminpanel:category_list')


@admin_staff_required
def order_list(request):
    orders = Order.objects.select_related('user').prefetch_related('items')
    paginator = Paginator(orders, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'adminpanel/order_list.html', {'page_obj': page_obj})
