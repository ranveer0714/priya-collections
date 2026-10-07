from .models import Category


def shop_context(request):
    cart = request.session.get('cart', {})
    wishlist = request.session.get('wishlist', [])
    cart_count = sum(int(quantity) for quantity in cart.values()) if isinstance(cart, dict) else 0
    wishlist_count = len(wishlist) if isinstance(wishlist, list) else 0

    return {
        'nav_categories': Category.objects.all(),
        'cart_count': cart_count,
        'wishlist_count': wishlist_count,
    }
