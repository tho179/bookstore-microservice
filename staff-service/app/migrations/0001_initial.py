from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Staff',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('department', models.CharField(default='operations', max_length=100)),
            ],
        ),
    ]
