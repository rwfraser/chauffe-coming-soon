from django.core.management.base import BaseCommand
from core.models import Product
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create the initial DLO license product'
    
    def handle(self, *args, **options):
        # Check if DLO product already exists
        existing_product = Product.objects.filter(name__icontains='DLO').first()
        
        if existing_product:
            self.stdout.write(
                self.style.WARNING(f'DLO product already exists: {existing_product.name}')
            )
            return
        
        # Create the DLO license product
        product = Product.objects.create(
            name='DLO (Designated Licensed Operator) License for 1 CHAUFFE Controller',
            description='Official DLO license for operating CHAUFFE blockchain controllers. Includes full access to blockchain operations and CHAUFFEcoin generation capabilities.',
            price=Decimal('0.10'),
            chauffecoins_included=100000,
            is_active=True
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created DLO product: {product.name}')
        )
        self.stdout.write(f'Price: ${product.price}')
        self.stdout.write(f'CHAUFFEcoins included: {product.chauffecoins_included:,}')