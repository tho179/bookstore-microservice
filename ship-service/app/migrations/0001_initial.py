from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Shipment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order_id", models.IntegerField()),
                ("customer_id", models.IntegerField()),
                ("address", models.TextField(blank=True, default="")),
                ("method", models.CharField(default="standard", max_length=40)),
                ("status", models.CharField(default="reserved", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
