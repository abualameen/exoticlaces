from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('lacesstore', '__latest__'),  # ✅ This will use the latest lacesstore migration
    ]

    operations = [
        migrations.CreateModel(
            name='Vendor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('business_name', models.CharField(max_length=200)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(max_length=20)),
                ('address', models.TextField(blank=True)),
                ('website', models.URLField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('commission_rate', models.DecimalField(decimal_places=2, default=10.0, max_digits=5)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['business_name'],
            },
        ),
        migrations.CreateModel(
            name='VendorProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=250, unique=True)),
                ('slug', models.SlugField(max_length=250, unique=True)),
                ('description', models.TextField(blank=True)),
                ('price', models.DecimalField(decimal_places=2, help_text='Selling price (includes your profit)', max_digits=10)),
                ('vendor_price', models.DecimalField(decimal_places=2, help_text='Price you pay to vendor', max_digits=10)),
                ('fabric_type', models.CharField(blank=True, max_length=100)),
                ('length', models.CharField(blank=True, help_text='e.g., 6 yards, 5 meters', max_length=50)),
                ('color', models.CharField(blank=True, max_length=50)),
                ('weight', models.CharField(blank=True, max_length=50)),
                ('material', models.CharField(blank=True, max_length=100)),
                ('origin', models.CharField(blank=True, help_text='Country of origin', max_length=100)),
                ('image', models.ImageField(blank=True, upload_to='vendor_products/')),
                ('additional_images', models.JSONField(blank=True, default=list)),
                ('stock', models.IntegerField(default=0)),
                ('available', models.BooleanField(default=True)),
                ('youtube_video_url', models.URLField(blank=True, help_text='Paste the full YouTube URL', max_length=500, null=True, verbose_name='YouTube Video URL')),
                ('youtube_video_id', models.CharField(blank=True, editable=False, max_length=50, null=True, verbose_name='YouTube Video ID')),
                ('estimated_delivery_min', models.IntegerField(default=5, help_text='Minimum delivery days')),
                ('estimated_delivery_max', models.IntegerField(default=10, help_text='Maximum delivery days')),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('active', 'Active'), ('inactive', 'Inactive'), ('out_of_stock', 'Out of Stock')], default='draft', max_length=20)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vendor_products', to='lacesstore.category')),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='vendor_products.vendor')),
            ],
            options={
                'verbose_name': 'Vendor Product',
                'verbose_name_plural': 'Vendor Products',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='VendorProductVariant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('color_name', models.CharField(max_length=50)),
                ('color_code', models.CharField(blank=True, max_length=20)),
                ('image', models.ImageField(upload_to='vendor_product_variants')),
                ('stock', models.IntegerField(default=0)),
                ('is_default', models.BooleanField(default=False)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='vendor_products.vendorproduct')),
            ],
            options={
                'unique_together': {('product', 'color_name')},
            },
        ),
        migrations.CreateModel(
            name='VendorOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(default=1)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('paystack_reference', models.CharField(blank=True, max_length=100)),
                ('paystack_access_code', models.CharField(blank=True, max_length=100)),
                ('payment_intent_id', models.CharField(blank=True, max_length=255)),
                ('status', models.CharField(choices=[('pending', 'Pending - Awaiting Vendor Confirmation'), ('secured', 'Secured - Item Purchased from Vendor'), ('shipped', 'Shipped to Customer'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled - Item Unavailable'), ('failed', 'Failed - Vendor Could Not Fulfill')], default='pending', max_length=20)),
                ('payment_status', models.CharField(choices=[('authorized', 'Authorized - Funds on Hold'), ('captured', 'Captured - Funds Collected'), ('refunded', 'Refunded'), ('failed', 'Failed')], default='authorized', max_length=20)),
                ('vendor_order_id', models.CharField(blank=True, max_length=100)),
                ('vendor_confirmed_at', models.DateTimeField(blank=True, null=True)),
                ('shipping_address', models.TextField()),
                ('country', models.CharField(blank=True, max_length=100)),
                ('state', models.CharField(blank=True, max_length=100)),
                ('shipping_method', models.CharField(blank=True, max_length=50)),
                ('shipping_cost', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('tracking_number', models.CharField(blank=True, max_length=100)),
                ('shipped_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vendor_orders', to='auth.user')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='vendor_products.vendorproduct')),
                ('variant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='vendor_products.vendorproductvariant')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
