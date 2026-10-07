from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Category, Order, OrderItem, Product


class CheckoutTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Rings')
        self.product = Product.objects.create(
            title='Gold Ring',
            price='1200.00',
            discount_price='1000.00',
            category=category,
        )
        session = self.client.session
        session['cart'] = {str(self.product.pk): 2}
        session.save()

    def test_checkout_creates_order_and_clears_cart(self):
        response = self.client.post(
            '/cart/checkout/',
            {
                'customer_name': 'Asha Customer',
                'email': 'asha@example.com',
                'phone': '9876543210',
                'address': '1 Market Road',
            },
        )

        self.assertEqual(response.status_code, 302)
        order = Order.objects.get()
        self.assertEqual(response.url, f'/order-confirmation/{order.confirmation_token}/')
        self.assertEqual(order.total_amount, Decimal('2000.00'))
        self.assertEqual(order.items.count(), 1)
        order_item = order.items.get()
        self.assertEqual(order_item.product, self.product)
        self.assertEqual(order_item.product_title, 'Gold Ring')
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(order_item.unit_price, Decimal('1000.00'))
        self.assertEqual(self.client.session.get('cart'), {})

    def test_confirmation_shows_success_and_order_contents(self):
        order = Order.objects.create(
            customer_name='Asha Customer',
            total_amount='1000.00',
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_title=self.product.title,
            quantity=1,
            unit_price='1000.00',
        )

        response = self.client.get(
            f'/order-confirmation/{order.confirmation_token}/'
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Order placed successfully!')
        self.assertContains(response, 'Gold Ring')
        self.assertContains(response, '#{}'.format(order.pk))

    def test_staff_orders_page_displays_purchased_products(self):
        order = Order.objects.create(
            customer_name='Asha Customer',
            total_amount='2000.00',
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_title=self.product.title,
            quantity=2,
            unit_price='1000.00',
        )
        staff_user = get_user_model().objects.create_user(
            username='staff',
            password='test-password',
            is_staff=True,
        )
        self.client.force_login(staff_user)

        response = self.client.get('/dashboard/orders/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gold Ring')
        self.assertContains(response, '&times; 2')

    def test_checkout_rejects_empty_cart(self):
        session = self.client.session
        session['cart'] = {}
        session.save()

        response = self.client.get('/cart/checkout/')

        self.assertRedirects(response, '/cart/')
        self.assertFalse(Order.objects.exists())
