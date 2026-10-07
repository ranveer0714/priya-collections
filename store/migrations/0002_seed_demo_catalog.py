from decimal import Decimal

from django.db import migrations


def seed_catalog(apps, schema_editor):
    Category = apps.get_model('store', 'Category')
    Product = apps.get_model('store', 'Product')

    if Product.objects.exists():
        return

    category_names = ['Necklace', 'Rings', 'Earrings', 'Bangles', 'Bracelets']
    categories = {}
    for name in category_names:
        category, _ = Category.objects.get_or_create(
            name=name,
            defaults={'slug': name.lower().replace(' ', '-')},
        )
        categories[name] = category

    products = [
        ('Choker Necklace Set', 'Necklace', Decimal('22999.00'), Decimal('18999.00')),
        ('Ruby Pearl Bridal Necklace', 'Necklace', Decimal('27899.00'), Decimal('23999.00')),
        ('Temple Jewellery Necklace', 'Necklace', Decimal('31999.00'), Decimal('27999.00')),
        ('Diamond Pendant Chain', 'Necklace', Decimal('17599.00'), Decimal('14999.00')),
        ('Pearl Strand Necklace', 'Necklace', Decimal('21999.00'), Decimal('17999.00')),
        ('Royal Kundan Ring', 'Rings', Decimal('28999.00'), Decimal('22999.00')),
        ('Solitaire Diamond Engagement Ring', 'Rings', Decimal('75999.00'), Decimal('67999.00')),
        ('Traditional Temple Gold Ring', 'Rings', Decimal('11999.00'), Decimal('9999.00')),
        ('Embellished Floral Cocktail Ring', 'Rings', Decimal('25999.00'), Decimal('20999.00')),
        ('Pearl & Polki Open-Stud Ring', 'Rings', Decimal('25999.00'), Decimal('21999.00')),
        ('Traditional Jhumka Earrings', 'Earrings', Decimal('39999.00'), Decimal('30999.00')),
        ('Classic Gold Bangles', 'Bangles', Decimal('34999.00'), Decimal('29999.00')),
    ]

    for title, category_name, price, discount_price in products:
        Product.objects.create(
            title=title,
            category=categories[category_name],
            price=price,
            discount_price=discount_price,
        )


def remove_seed_catalog(apps, schema_editor):
    Product = apps.get_model('store', 'Product')
    titles = [
        'Choker Necklace Set',
        'Ruby Pearl Bridal Necklace',
        'Temple Jewellery Necklace',
        'Diamond Pendant Chain',
        'Pearl Strand Necklace',
        'Royal Kundan Ring',
        'Solitaire Diamond Engagement Ring',
        'Traditional Temple Gold Ring',
        'Embellished Floral Cocktail Ring',
        'Pearl & Polki Open-Stud Ring',
        'Traditional Jhumka Earrings',
        'Classic Gold Bangles',
    ]
    Product.objects.filter(title__in=titles).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('store', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_catalog, remove_seed_catalog),
    ]
