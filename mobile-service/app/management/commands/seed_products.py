from django.core.management.base import BaseCommand
from app.models import MobileProduct


class Command(BaseCommand):
    help = 'Seed sample mobile products'

    def handle(self, *args, **options):
        seeds = [
            {
                'name': 'SmartPhone Nova X',
                'description': 'Dien thoai man hinh 6.7 inch, camera 50MP.',
                'price': '13990000',
                'stock': 22,
                'brand': 'Nova',
                'model_code': 'NVX-2026',
                'warranty_months': 18,
                'specs': {'ram': '8GB', 'storage': '256GB', 'chip': 'Snapdragon'},
                'image_url': 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9',
            },
            {
                'name': 'SmartPhone Lite 5G',
                'description': 'Mobile tam trung, pin 5000mAh, sac nhanh 45W.',
                'price': '7990000',
                'stock': 35,
                'brand': 'LitePhone',
                'model_code': 'LP5G-2026',
                'warranty_months': 12,
                'specs': {'ram': '6GB', 'storage': '128GB', 'battery': '5000mAh'},
                'image_url': 'https://images.unsplash.com/photo-1598327105666-5b89351aff97',
            },
        ]

        created = 0
        for payload in seeds:
            _, was_created = MobileProduct.objects.get_or_create(name=payload['name'], defaults=payload)
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f'Seeded mobile products. Created: {created}'))
