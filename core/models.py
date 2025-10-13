from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import json


class Product(models.Model):
    """Product model for DLO licenses and other items"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    chauffecoins_included = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']


class Order(models.Model):
    """Order model to track purchases"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    stripe_payment_intent_id = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} - {self.user.username} - ${self.total_amount}"

    class Meta:
        ordering = ['-created_at']


class License(models.Model):
    """DLO License model for tracking user licenses"""
    LICENSE_STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='licenses')
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='license')
    license_number = models.CharField(max_length=50, unique=True, blank=True)
    controller_name = models.CharField(max_length=200, blank=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    existing_licenses = models.TextField(blank=True)
    dloid_parameters = models.TextField(blank=True)  # JSON string of DLOID params
    status = models.CharField(max_length=20, choices=LICENSE_STATUS_CHOICES, default='active')
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"License {self.license_number} - {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.license_number:
            # Generate unique license number
            import random
            import string
            while True:
                license_num = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
                if not License.objects.filter(license_number=license_num).exists():
                    self.license_number = license_num
                    break
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-issued_at']


class CHAUFFEcoinTransaction(models.Model):
    """Track CHAUFFEcoin transactions and balances"""
    TRANSACTION_TYPES = [
        ('earned', 'Earned'),
        ('spent', 'Spent'),
        ('bonus', 'Bonus'),
        ('refund', 'Refund'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chauffe_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.IntegerField()  # CHAUFFEcoins amount
    description = models.CharField(max_length=200)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - {self.amount} CHAUFFEcoins"

    class Meta:
        ordering = ['-created_at']


class UserProfile(models.Model):
    """Extended user profile for CHAUFFEcoin balance and other info"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    chauffecoins_balance = models.IntegerField(default=0)
    total_licenses_purchased = models.IntegerField(default=0)
    blockchain_references = models.TextField(default='{}', blank=True)  # Store DLOID and blockchain info as JSON
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.chauffecoins_balance} CHAUFFEcoins"
    
    def get_uuid_string(self):
        """Get UUID as string for blockchain operations"""
        return str(self.uuid)
    
    def add_blockchain_reference(self, dloid, blockchain_info):
        """Add a DLOID and blockchain reference to this user"""
        try:
            references = json.loads(self.blockchain_references or '{}')
        except json.JSONDecodeError:
            references = {}
        
        references[dloid] = {
            'dloid': dloid,
            'blockchain_info': blockchain_info,
            'created_at': timezone.now().isoformat()
        }
        
        self.blockchain_references = json.dumps(references)
        self.save()
    
    def get_blockchain_references(self):
        """Get all blockchain references for this user"""
        try:
            return json.loads(self.blockchain_references or '{}')
        except json.JSONDecodeError:
            return {}

    def update_balance(self, amount, transaction_type, description, order=None):
        """Update CHAUFFEcoin balance and create transaction record"""
        if transaction_type in ['earned', 'bonus', 'refund']:
            self.chauffecoins_balance += amount
        elif transaction_type == 'spent':
            self.chauffecoins_balance -= amount
        
        self.save()
        
        # Create transaction record
        CHAUFFEcoinTransaction.objects.create(
            user=self.user,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            order=order
        )
