from django import forms
from django.utils.translation import gettext_lazy as _
from .models import *
from django.contrib.auth.forms import (
    AuthenticationForm, 
    PasswordResetForm as AuthPasswordResetForm,
    SetPasswordForm,
    PasswordChangeForm as AuthPasswordChangeForm
)
from django.core.validators import validate_email, RegexValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import password_validation



class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Username',
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5',
            'placeholder': 'Enter your username',
            'autocomplete': 'username'
        }),
        max_length=150
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5',
            'placeholder': '••••••••',
            'autocomplete': 'current-password'
        })
    )
    remember = forms.BooleanField(
        label='Remember me',
        required=False,
        initial=True,  # Default to checked
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'autofocus': True})


class UserRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(
        label='First Name',
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5',
            'placeholder': 'John',
            'autocomplete': 'given-name'
        }),
        max_length=30,
        required=True
    )
    
    last_name = forms.CharField(
        label='Last Name',
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5',
            'placeholder': 'Doe',
            'autocomplete': 'family-name'
        }),
        max_length=30,
        required=True
    )
    
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full pl-10 p-2.5',
            'placeholder': 'your@email.com',
            'autocomplete': 'email'
        }),
        required=True
    )
    
    phone = forms.CharField(
        label='Phone Number',
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full pl-10 p-2.5',
            'placeholder': '+1 (555) 123-4567',
            'autocomplete': 'tel'
        }),
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )],
        required=True
    )
    
    username = forms.CharField(
        label='Username',
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full pl-10 p-2.5',
            'placeholder': 'johndoe',
            'autocomplete': 'username'
        }),
        max_length=150,
        required=True
    )
    
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full pl-10 p-2.5',
            'placeholder': '••••••••',
            'autocomplete': 'new-password'
        }),
        validators=[validate_password],
        required=True
    )
    
    confirm_password = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full pl-10 p-2.5',
            'placeholder': '••••••••',
            'autocomplete': 'new-password'
        }),
        required=True
    )
    
    terms = forms.BooleanField(
        label='I agree to the terms and conditions',
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
        }),
        required=True
    )
    
    newsletter = forms.BooleanField(
        label='Subscribe to newsletter',
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
        }),
        required=False,
        initial=True
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'username', 'password']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email address is already in use.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class PasswordResetForm(AuthPasswordResetForm):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5',
            'placeholder': 'your@email.com',
            'autocomplete': 'email'
        }),
        max_length=254
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email__iexact=email, is_active=True).exists():
            raise ValidationError(_("There is no user registered with this email address."))
        return email


class SetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5',
            'placeholder': '••••••••',
            'autocomplete': 'new-password'
        }),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label=_("New password confirmation"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5',
            'placeholder': '••••••••',
            'autocomplete': 'new-password'
        }),
    )


class PasswordChangeForm(AuthPasswordChangeForm):
    old_password = forms.CharField(
        label=_("Current password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5',
            'placeholder': '••••••••',
            'autocomplete': 'current-password'
        }),
    )
    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5',
            'placeholder': '••••••••',
            'autocomplete': 'new-password'
        }),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label=_("New password confirmation"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5',
            'placeholder': '••••••••',
            'autocomplete': 'new-password'
        }),
    )


class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        label='First Name',
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5',
            'placeholder': 'John'
        }),
        max_length=30,
        required=True
    )
    
    last_name = forms.CharField(
        label='Last Name',
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5',
            'placeholder': 'Doe'
        }),
        max_length=30,
        required=True
    )
    
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full pl-10 p-2.5',
            'placeholder': 'your@email.com'
        }),
        required=True
    )
    
    phone = forms.CharField(
        label='Phone Number',
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full pl-10 p-2.5',
            'placeholder': '+1 (555) 123-4567'
        }),
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )],
        required=True
    )
    
    profile_picture = forms.ImageField(
        label='Profile Picture',
        widget=forms.FileInput(attrs={
            'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
        }),
        required=False
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].disabled = True  # Email shouldn't be changed after registration

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("This email address is already in use.")
        return email
    






class BaseReviewForm(forms.ModelForm):
    RATING_CHOICES = [
        (5, '5 - Excellent'),
        (4, '4 - Good'),
        (3, '3 - Average'),
        (2, '2 - Fair'),
        (1, '1 - Poor'),
    ]
    
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'hidden'}),
        label=_('Overall Rating'),
        required=True
    )
    
    title = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white',
            'placeholder': _('Summarize your experience')
        }),
        label=_('Review Title'),
        required=True
    )
    
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white',
            'rows': 4,
            'placeholder': _('Share details about your experience...')
        }),
        label=_('Your Review'),
        required=True
    )
    
    class Meta:
        fields = ['rating', 'title', 'comment']


class ProjectReviewForm(forms.ModelForm):
    RATING_CHOICES = [
        (5, '5 - Excellent'),
        (4, '4 - Good'),
        (3, '3 - Average'),
        (2, '2 - Fair'),
        (1, '1 - Poor'),
    ]
    
    # Main fields
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'hidden'}),
        label=_('Overall Rating'),
        required=True
    )
    
    title = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': _('Summarize your experience')
        }),
        label=_('Review Title'),
        required=True
    )
    
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500',
            'rows': 6,
            'placeholder': _('Share your honest thoughts about the property...')
        }),
        label=_('Detailed Review'),
        required=True
    )
    
    # Category ratings
    design_rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'hidden'}),
        label=_('Design & Architecture'),
        required=True
    )
    
    location_rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'hidden'}),
        label=_('Location'),
        required=True
    )
    
    amenities_rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'hidden'}),
        label=_('Amenities'),
        required=True
    )
    
    quality_rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'hidden'}),
        label=_('Construction Quality'),
        required=True
    )
    
    value_rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'hidden'}),
        label=_('Value for Money'),
        required=True
    )

    class Meta:
        model = ProjectReview
        fields = [
            'rating', 'title', 'comment',
            'design_rating', 'location_rating', 
            'amenities_rating', 'quality_rating',
            'value_rating'
        ]
    
    def clean(self):
        cleaned_data = super().clean()
        # Ensure all ratings are between 1-5
        for field in ['rating', 'design_rating', 'location_rating', 'amenities_rating', 'quality_rating', 'value_rating']:
            if field in cleaned_data:
                try:
                    rating = int(cleaned_data[field])
                    if rating < 1 or rating > 5:
                        self.add_error(field, 'Rating must be between 1 and 5')
                except (ValueError, TypeError):
                    self.add_error(field, 'Invalid rating value')
        
        # Validate title and comment lengths
        if len(cleaned_data.get('title', '')) < 5:
            self.add_error('title', 'Title must be at least 10 characters long')
        
        if len(cleaned_data.get('comment', '')) < 20:
            self.add_error('comment', 'Review must be at least 50 characters long')
        
        return cleaned_data



class PropertyReviewForm(BaseReviewForm):
    condition_rating = forms.ChoiceField(
        choices=BaseReviewForm.RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'hidden'}),
        label=_('Condition Rating'),
        required=True
    )
    
    neighborhood_rating = forms.ChoiceField(
        choices=BaseReviewForm.RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'hidden'}),
        label=_('Neighborhood Rating'),
        required=True
    )
    
    value_rating = forms.ChoiceField(
        choices=BaseReviewForm.RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'hidden'}),
        label=_('Value for Money Rating'),
        required=True
    )
    
    move_in_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white',
            'type': 'date'
        }),
        label=_('Move In Date'),
        required=False
    )
    
    move_out_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white',
            'type': 'date'
        }),
        label=_('Move Out Date'),
        required=False
    )
    
    class Meta(BaseReviewForm.Meta):
        model = PropertyReview
        fields = BaseReviewForm.Meta.fields + [
            'condition_rating',
            'neighborhood_rating',
            'value_rating',
            'category',
            'move_in_date',
            'move_out_date'
        ]
    
    def clean(self):
        cleaned_data = super().clean()
        move_in_date = cleaned_data.get('move_in_date')
        move_out_date = cleaned_data.get('move_out_date')
        
        if move_out_date and move_in_date and move_out_date < move_in_date:
            raise forms.ValidationError(_("Move out date cannot be before move in date"))
        
        return cleaned_data