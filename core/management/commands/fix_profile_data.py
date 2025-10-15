from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import UserProfile, License, CHAUFFEcoinTransaction, Order
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Fix profile data inconsistencies - recalculate license counts and CHAUFFEcoin balances'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Fix data for specific user (by username)',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        target_user = options.get('user')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        # Get users to process
        if target_user:
            try:
                users = [User.objects.get(username=target_user)]
                self.stdout.write(f"Processing user: {target_user}")
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"User '{target_user}' not found")
                )
                return
        else:
            users = User.objects.all()
            self.stdout.write(f"Processing all {users.count()} users")
        
        fixed_users = 0
        total_issues = 0
        
        for user in users:
            issues_found = []
            
            # Get or create user profile
            user_profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'chauffecoins_balance': 0}
            )
            
            if created:
                issues_found.append("Created missing UserProfile")
            
            # Calculate actual license count
            actual_license_count = License.objects.filter(user=user).count()
            stored_license_count = user_profile.total_licenses_purchased
            
            if actual_license_count != stored_license_count:
                issues_found.append(
                    f"License count mismatch: stored={stored_license_count}, actual={actual_license_count}"
                )
                if not dry_run:
                    user_profile.total_licenses_purchased = actual_license_count
            
            # Calculate actual CHAUFFEcoin balance from transactions
            transactions = CHAUFFEcoinTransaction.objects.filter(user=user)
            calculated_balance = 0
            
            for transaction in transactions:
                if transaction.transaction_type in ['earned', 'bonus', 'refund']:
                    calculated_balance += transaction.amount
                elif transaction.transaction_type == 'spent':
                    calculated_balance -= transaction.amount
            
            stored_balance = user_profile.chauffecoins_balance
            
            if calculated_balance != stored_balance:
                issues_found.append(
                    f"CHAUFFEcoin balance mismatch: stored={stored_balance}, calculated={calculated_balance}"
                )
                if not dry_run:
                    user_profile.chauffecoins_balance = calculated_balance
            
            # Check for orders missing licenses
            completed_orders = Order.objects.filter(user=user, status='completed')
            missing_licenses = 0
            
            for order in completed_orders:
                existing_licenses = License.objects.filter(order=order).count()
                expected_licenses = order.quantity
                
                if existing_licenses < expected_licenses:
                    licenses_to_create = expected_licenses - existing_licenses
                    missing_licenses += licenses_to_create
                    
                    if not dry_run:
                        for i in range(licenses_to_create):
                            License.objects.create(
                                user=user,
                                order=order
                            )
            
            if missing_licenses > 0:
                issues_found.append(f"Created {missing_licenses} missing licenses")
            
            # Save changes if any
            if issues_found and not dry_run:
                user_profile.save()
                fixed_users += 1
                
            # Report issues for this user
            if issues_found:
                total_issues += len(issues_found)
                self.stdout.write(f"\n{user.username} ({user.email}):")
                for issue in issues_found:
                    if dry_run:
                        self.stdout.write(f"  WOULD FIX: {issue}")
                    else:
                        self.stdout.write(f"  FIXED: {issue}")
        
        # Summary
        self.stdout.write(f"\n" + "="*50)
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"DRY RUN COMPLETE: Found {total_issues} issues across {len([u for u in users if any(self._get_user_issues(u))])} users")
            )
            self.stdout.write("Run without --dry-run to fix these issues")
        else:
            self.stdout.write(
                self.style.SUCCESS(f"FIXED: {total_issues} issues across {fixed_users} users")
            )
        
        self.stdout.write("="*50)
    
    def _get_user_issues(self, user):
        """Helper to check if user has issues (for dry run counting)"""
        issues = []
        
        try:
            user_profile = user.profile
        except:
            return ["Missing UserProfile"]
        
        actual_license_count = License.objects.filter(user=user).count()
        if actual_license_count != user_profile.total_licenses_purchased:
            issues.append("License count mismatch")
        
        # Check CHAUFFEcoin balance
        transactions = CHAUFFEcoinTransaction.objects.filter(user=user)
        calculated_balance = sum(
            t.amount if t.transaction_type in ['earned', 'bonus', 'refund'] else -t.amount
            for t in transactions
        )
        
        if calculated_balance != user_profile.chauffecoins_balance:
            issues.append("CHAUFFEcoin balance mismatch")
        
        # Check missing licenses
        completed_orders = Order.objects.filter(user=user, status='completed')
        for order in completed_orders:
            existing_licenses = License.objects.filter(order=order).count()
            if existing_licenses < order.quantity:
                issues.append("Missing licenses")
                break
        
        return issues