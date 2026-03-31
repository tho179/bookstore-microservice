from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("customer_id", models.IntegerField()),
                ("total_amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("payment_method", models.CharField(default="cod", max_length=40)),
                ("shipping_method", models.CharField(default="standard", max_length=40)),
                ("shipping_address", models.TextField(blank=True, default="")),
                ("payment_id", models.IntegerField(blank=True, null=True)),
                ("shipment_id", models.IntegerField(blank=True, null=True)),
                ("status", models.CharField(default="pending", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("product_id", models.IntegerField()),
                ("name", models.CharField(max_length=255)),
                ("category", models.CharField(blank=True, default="", max_length=60)),
                ("price", models.DecimalField(decimal_places=2, max_digits=12)),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("line_total", models.DecimalField(decimal_places=2, max_digits=12)),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="app.order")),
            ],
        ),
    ]
