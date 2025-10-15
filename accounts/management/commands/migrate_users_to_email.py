from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


class Command(BaseCommand):
    help = 'Migrate existing users to email-based usernames'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making actual changes',
        )
        parser.add_argument(
            '--auto-email',
            action='store_true',
            help='Automatically create email addresses for users without them (username@example.com)',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        auto_email = options['auto_email']
        
        self.stdout.write(self.style.SUCCESS('=== User Email Migration Analysis ==='))
        
        # Get all users
        users = User.objects.all()
        total_users = users.count()
        
        # Categorize users
        users_with_email_username = []
        users_with_email_field = []
        users_without_email = []
        
        for user in users:
            # Check if username is already a valid email
            try:
                validate_email(user.username)
                users_with_email_username.append(user)
            except ValidationError:
                # Username is not an email, check if email field is set
                if user.email:
                    try:
                        validate_email(user.email)
                        users_with_email_field.append(user)
                    except ValidationError:
                        users_without_email.append(user)
                else:
                    users_without_email.append(user)
        
        self.stdout.write(f'Total users: {total_users}')
        self.stdout.write(f'Users with email as username: {len(users_with_email_username)}')
        self.stdout.write(f'Users with separate email field: {len(users_with_email_field)}')
        self.stdout.write(f'Users without valid email: {len(users_without_email)}')
        self.stdout.write('')
        
        # Show details for each category
        if users_with_email_username:
            self.stdout.write(self.style.SUCCESS('✅ Users already using email as username:'))
            for user in users_with_email_username:
                self.stdout.write(f'  - {user.username} (ID: {user.id})')
        
        if users_with_email_field:
            self.stdout.write(self.style.WARNING('⚠️  Users who can be migrated (have email field):'))
            for user in users_with_email_field:
                self.stdout.write(f'  - {user.username} → {user.email} (ID: {user.id})')
        
        if users_without_email:
            self.stdout.write(self.style.ERROR('❌ Users without valid email addresses:'))
            for user in users_without_email:
                email_suggestion = f"{user.username}@example.com" if auto_email else "NEEDS EMAIL"
                self.stdout.write(f'  - {user.username} → {email_suggestion} (ID: {user.id})')
        
        self.stdout.write('')
        
        # Perform migrations if not dry run
        if not dry_run:
            self.stdout.write('=== Performing Migration ===')
            
            # Migrate users with email field
            for user in users_with_email_field:
                old_username = user.username
                new_username = user.email.lower().strip()
                
                # Check if the new username already exists
                if User.objects.filter(username=new_username).exclude(id=user.id).exists():
                    self.stdout.write(
                        self.style.ERROR(
                            f'❌ Cannot migrate {old_username} → {new_username}: '
                            'Email already in use as username'
                        )
                    )
                    continue
                
                user.username = new_username
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Migrated: {old_username} → {new_username}')
                )
            
            # Handle users without email
            if auto_email:
                for user in users_without_email:
                    old_username = user.username
                    new_username = f"{user.username}@example.com".lower()
                    
                    # Check if the new username already exists
                    if User.objects.filter(username=new_username).exclude(id=user.id).exists():
                        # Try with user ID appended
                        new_username = f"{user.username}_{user.id}@example.com".lower()
                    
                    user.username = new_username
                    user.email = new_username
                    user.save()
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠️  Auto-generated email: {old_username} → {new_username}'
                        )
                    )
            else:
                if users_without_email:
                    self.stdout.write(
                        self.style.ERROR(
                            f'❌ {len(users_without_email)} users need email addresses. '
                            'Use --auto-email to generate placeholder emails, or update manually.'
                        )
                    )
        else:
            self.stdout.write(self.style.WARNING('This was a dry run. Use without --dry-run to apply changes.'))
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Migration analysis complete!'))