from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


class EmailUserCreationForm(UserCreationForm):
    """
    Custom user creation form that requires the username to be a valid email address.
    """
    
    username = forms.EmailField(
        label='Email Address',
        max_length=254,
        help_text='Enter a valid email address. This will be your username.',
        widget=forms.EmailInput(attrs={
            'placeholder': 'your.email@example.com',
            'autocomplete': 'email'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update field attributes for better UX
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'required': True,
            'type': 'email'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'required': True
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'required': True
        })
    
    def clean_username(self):
        """
        Validate that the username is a valid email address.
        """
        username = self.cleaned_data.get('username')
        
        if not username:
            raise ValidationError('Email address is required.')
        
        # Validate email format
        try:
            validate_email(username)
        except ValidationError:
            raise ValidationError('Please enter a valid email address.')
        
        # Convert to lowercase for consistency
        username = username.lower().strip()
        
        # Check if email is already in use
        if User.objects.filter(username=username).exists():
            raise ValidationError(
                'An account with this email address already exists. '
                'Please use a different email or try signing in.'
            )
        
        # Also set the email field to the same value
        return username
    
    def save(self, commit=True):
        """
        Save the user with email set to the same value as username.
        """
        user = super().save(commit=False)
        # Set both username and email to the same value
        user.username = self.cleaned_data['username'].lower().strip()
        user.email = user.username
        
        if commit:
            user.save()
        return user


class EmailAuthenticationForm(AuthenticationForm):
    """
    Custom authentication form that shows 'Email Address' as the username label.
    """
    
    username = forms.EmailField(
        label='Email Address',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'placeholder': 'your.email@example.com',
            'autocomplete': 'email',
            'class': 'form-control'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update password field attributes
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    
    def clean_username(self):
        """
        Convert username to lowercase for consistent login.
        """
        username = self.cleaned_data.get('username')
        if username:
            return username.lower().strip()
        return username
