from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order_id", models.IntegerField()),
                ("customer_id", models.IntegerField()),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("method", models.CharField(default="cod", max_length=40)),
                ("status", models.CharField(default="reserved", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
