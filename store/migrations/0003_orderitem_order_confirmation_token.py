import uuid

import django.db.models.deletion
from django.db import migrations, models


def populate_confirmation_tokens(apps, schema_editor):
    Order = apps.get_model('store', 'Order')
    for order in Order.objects.filter(confirmation_token__isnull=True).iterator():
        order.confirmation_token = uuid.uuid4()
        order.save(update_fields=['confirmation_token'])


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0002_seed_demo_catalog'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='confirmation_token',
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.RunPython(
            populate_confirmation_tokens,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='order',
            name='confirmation_token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_title', models.CharField(max_length=180)),
                ('quantity', models.PositiveIntegerField()),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='store.order')),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='store.product')),
            ],
        ),
    ]
