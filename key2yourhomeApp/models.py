from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.fields import ArrayField
from decimal import Decimal
import uuid
from datetime import datetime, timezone
from django.core.exceptions import ValidationError
from django.contrib.postgres.indexes import GinIndex
from django.urls import reverse
from django.utils import timezone
from django.db import models
from django.db.models import Avg, Count
from django.utils.translation import gettext_lazy as _
from django.utils.crypto import get_random_string
from django.contrib.auth.models import AbstractUser
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.postgres.search import SearchVector



class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    password_reset_token = models.CharField(max_length=100, blank=True, null=True)
    password_reset_expires = models.DateTimeField(blank=True, null=True)
    last_password_change = models.DateTimeField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    def __str__(self):
        return self.email

    
    def send_password_reset_email(self, request):
        token = get_random_string(50)
        self.password_reset_token = token
        self.password_reset_expires = timezone.now() + timezone.timedelta(hours=1)
        self.save()
        
        reset_url = request.build_absolute_uri(
            reverse('reset_password', kwargs={'token': token})
        )
        
        subject = 'Password Reset Request'
        html_message = render_to_string('auth/password_reset.html', {
            'user': self,
            'reset_url': reset_url,
            'expiry_hours': 1,
            'site_name': settings.SITE_NAME,
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
            html_message=html_message,
            fail_silently=False
        )
    
    @property
    def bookmarked_projects(self):
        """Returns all projects bookmarked by this user"""
        return Project.objects.filter(bookmarks__user=self)
    
    @property
    def bookmarked_properties(self):
        """Returns all properties bookmarked by this user"""
        return Property.objects.filter(bookmarks__user=self)

class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    remember_me = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('user', 'session_key')
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
        ordering = ['-last_activity']
        
    
    def __str__(self):
        return f"{self.user.email} - {self.session_key}"
    
class PasswordChangeHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_history')
    password = models.CharField(max_length=128)  # Stores the hashed password
    changed_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Password Change History'
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.changed_at}"  
    
class SearchQueryLog(models.Model):
    """Log all search queries for analytics and suggestions"""
    SEARCH_TYPES = (
        ('PROPERTY', 'Property'),
        ('PROJECT', 'Project'),
        ('GENERAL', 'General'),
    )
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    search_type = models.CharField(max_length=10, choices=SEARCH_TYPES)
    query = models.JSONField()  # Stores all search parameters
    results_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
            models.Index(fields=['search_type']),
        ]

class SearchSuggestion(models.Model):
    """Store popular search terms and suggestions"""
    term = models.CharField(max_length=255, db_index=True)
    search_type = models.CharField(max_length=10, choices=SearchQueryLog.SEARCH_TYPES)
    weight = models.FloatField(default=1.0)  # For ranking suggestions
    last_used = models.DateTimeField(auto_now=True)
    use_count = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('term', 'search_type')
        ordering = ['-weight', '-use_count']
        
    def increment_use(self):
        self.use_count += 1
        self.weight = self.use_count * 0.8  # Adjust weight formula as needed
        self.save()

class CookieConsent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    consent_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
        ]
        verbose_name = "Cookie Consent"
        verbose_name_plural = "Cookie Consents"

    def __str__(self):
        return f"Cookie consent for {self.user or 'anonymous'}"

class BaseModel(models.Model):
    """Abstract base model with common fields"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class Flooring(BaseModel):
    """Model representing different types of flooring"""
    name = models.CharField(
        max_length=100,
        unique=True,
        null=False,
        blank=False,
        validators=[MinLengthValidator(2)],
        help_text="Name of the flooring (2-100 characters)"
    )
    
    def __str__(self):
        return self.name
    
    def clean(self):
        if not self.name:
            raise ValidationError(_("Flooring name cannot be empty"))
        self.name = self.name.strip()
    
    class Meta:
        verbose_name = "Flooring"
        verbose_name_plural = "Floorings"
        ordering = ['name']

class Parking(BaseModel):
    """Model representing different types of parking"""
    type = models.CharField(
        max_length=100,
        unique=True,
        null=False,
        blank=False,
        validators=[MinLengthValidator(2)],
        help_text="Type of parking (2-100 characters)"
    )
    
    def __str__(self):
        return self.type
    
    def clean(self):
        if not self.type:
            raise ValidationError(_("Parking type cannot be empty"))
        self.type = self.type.strip()
    
    class Meta:
        verbose_name = "Parking"
        verbose_name_plural = "Parkings"
        ordering = ['type']

class Amenity(BaseModel):
    """Model representing amenities available in properties or projects"""
    name = models.CharField(
        max_length=100,
        unique=True,
        null=False,
        blank=False,
        help_text="Name of the amenity"
    )
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Amenity"
        verbose_name_plural = "Amenities"
        ordering = ['name']

class Highlight(BaseModel):
    """Model representing highlights/features of properties or projects"""
    name = models.CharField(
        max_length=100,
        unique=True,
        null=False,
        blank=False,
        help_text="Name of the highlight"
    )
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Highlight"
        verbose_name_plural = "Highlights"
        ordering = ['name']

class NearbyPlace(BaseModel):
    """Model representing nearby places to properties or projects"""
    name = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        help_text="Name of the nearby place (e.g., Hospital, School, Park)"
    )
    distance = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=False,
        blank=False,
        help_text="Distance from the property/project in kilometers"
    )
    
    def __str__(self):
        return f"{self.name} ({self.distance} km)"
    
    class Meta:
        verbose_name = "Nearby Place"
        verbose_name_plural = "Nearby Places"
        ordering = ['name']
        unique_together = ['name', 'distance']

class Overlooking(BaseModel):
    """Model representing what a property overlooks"""
    name = models.CharField(
        max_length=100,
        unique=True,
        null=False,
        blank=False,
        help_text="What the property overlooks"
    )
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Overlooking"
        verbose_name_plural = "Overlookings"
        ordering = ['name']

class Furnishing(BaseModel):
    """Model representing furnishings available in properties"""
    name = models.CharField(
        max_length=100,
        unique=True,
        null=False,
        blank=False,
        help_text="Name of the furnishing item"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Quantity of the furnishing item"
    )
    
    def __str__(self):
        return f"{self.name} (x{self.quantity})"
    
    class Meta:
        verbose_name = "Furnishing"
        verbose_name_plural = "Furnishings"
        ordering = ['name']

class Media(BaseModel):
    """Model representing media files (images, videos) for properties and projects"""
    class MediaType(models.TextChoices):
        IMAGE = 'IMAGE', _('Image')
        VIDEO = 'VIDEO', _('Video')
        FILE = 'FILE', _('File')
    
    title = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        help_text="Title of the media"
    )
    about = models.TextField(
        max_length=1000,
        blank=True,
        help_text="Description about the media"
    )
    media_type = models.CharField(
        max_length=10,
        choices=MediaType.choices,
        null=False,
        blank=False,
        help_text="Type of media"
    )
    file = models.FileField(
        upload_to='real_estate_media/',
        null=False,
        blank=False,
        help_text="Upload media file"
    )
    
    # Relationships
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='media'
    )
    property = models.ForeignKey(
        'Property',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='media'
    )
    
    def __str__(self):
        return f"{self.title} ({self.get_media_type_display()})"
    
    def clean(self):
        # Skip validation if we're in the middle of saving (helps with admin inline saving)
        if getattr(self, '_in_save', False):
            return
            
        if not self.project and not self.property:
            raise ValidationError({
                'project': 'Media must be associated with either a project or property',
                'property': 'Media must be associated with either a project or property'
            })
        if self.project and self.property:
            raise ValidationError({
                'project': 'Media can only be associated with one entity',
                'property': 'Media can only be associated with one entity'
            })

    def save(self, *args, **kwargs):
        self._in_save = True
        try:
            self.full_clean()
            super().save(*args, **kwargs)
        finally:
            self._in_save = False
    
    class Meta:
        verbose_name = "Media"
        verbose_name_plural = "Media"
        ordering = ['-created_at']

class Phase(BaseModel):
    """Model representing phases of a project"""
    class NumberOfBedrooms(models.TextChoices):
        ONE_BHK = '1BHK', _('1 BHK')
        TWO_BHK = '2BHK', _('2 BHK')
        THREE_BHK = '3BHK', _('3 BHK')
        FOUR_BHK = '4BHK', _('4 BHK')
        FIVE_BHK = '5BHK', _('5 BHK')
        SIX_BHK = '6BHK', _('6 BHK')
        SEVEN_BHK = '7BHK', _('7 BHK')
        EIGHT_BHK = '8BHK', _('8 BHK')
        NINE_BHK = '9BHK', _('9 BHK')
        MORE_THAN_NINE_BHK = '9+_BHK', _('9+ BHK')
    
    class ConstructionStatus(models.TextChoices):
        UPCOMING = 'UPCOMING', _('Upcoming')
        UNDER_CONSTRUCTION = 'UNDER_CONSTRUCTION', _('Under Construction')
        PHASE_1_COMPLETED = 'PHASE_1_COMPLETED', _('Phase 1 Completed')
        PHASE_2_COMPLETED = 'PHASE_2_COMPLETED', _('Phase 2 Completed')
        LAST_PHASE_PENDING = 'LAST_PHASE_PENDING', _('Last Phase Pending')
        READY_TO_MOVE = 'READY_TO_MOVE', _('Ready to Move')
        PARTIALLY_READY_TO_MOVE = 'PARTIALLY_READY_TO_MOVE', _('Partially Ready to Move')
        NEW_LAUNCH = 'NEW_LAUNCH', _('New Launch')
    
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        related_name='phases',
        null=False,
        blank=False
    )
    phase_name = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        help_text="Name of the phase (e.g., Phase 1, Phase 2)"
    )
    number_of_towers = models.PositiveIntegerField(
        null=False,
        blank=False,
        help_text="Number of towers in this phase"
    )
    construction_status = models.CharField(
        max_length=120,
        choices=ConstructionStatus.choices,
        null=False,
        blank=False,
        help_text="Current construction status of the phase"
    )
    possession = models.DateField(
        null=False,
        blank=False,
        help_text="Estimated possession date"
    )
    completion_year = models.DateField(
        null=False,
        blank=False,
        help_text="Estimated completion year"
    )
    number_of_bedrooms = models.CharField(
        max_length=10,
        choices=NumberOfBedrooms.choices,
        null=False,
        blank=False,
        help_text="Number of bedrooms configuration"
    )
    
    def __str__(self):
        return f"{self.project.name} - {self.phase_name}"
    
    class Meta:
        verbose_name = "Phase"
        verbose_name_plural = "Phases"
        ordering = ['project', 'phase_name']
        unique_together = ['project', 'phase_name']

class Project(BaseModel):
    """Model representing a real estate project"""
    class PropertyType(models.TextChoices):
        RESIDENTIAL_APARTMENT = 'RESIDENTIAL_APARTMENT', _('Residential Apartment')
        INDEPENDENT_BUILDER_FLOOR = 'INDEPENDENT_BUILDER_FLOOR', _('Independent/Builder Floor')
        INDEPENDENT_HOUSE_VILLA = 'INDEPENDENT_HOUSE_VILLA', _('Independent House/Villa')
        RESIDENTIAL_LAND = 'RESIDENTIAL_LAND', _('Residential Land')
        STUDIO_APARTMENT = 'STUDIO_APARTMENT', _('1 RK/Studio Apartment')
        FARMHOUSE = 'FARMHOUSE', _('Farm House')
        SERVICED_APARTMENTS = 'SERVICED_APARTMENTS', _('Serviced Apartments')
        OTHER = 'OTHER', _('Other')
        OFFICE_SPACES = 'OFFICE_SPACES', _('Office Spaces')
        READY_TO_MOVE = 'READY_TO_MOVE', _('Ready to Move')
        BARESHELL = 'BARESHELL', _('BareShell')
        CO_WORKING = 'CO_WORKING', _('Co-Working')
        RETAIL_SHOPS_SHOWROOMS = 'RETAIL_SHOPS_SHOWROOMS', _('Retail Shops/Showrooms')
        SHOPS = 'SHOPS', _('Shops')
        SHOWROOMS = 'SHOWROOMS', _('Showrooms')
        OTHER_COMMERCIAL_SPACES = 'OTHER_COMMERCIAL_SPACES', _('Other Commercial Spaces')
        COMMERCIAL_LAND_INST_LAND = 'COMMERCIAL_LAND_INST_LAND', _('Commercial/Inst. Land')
        INDUSTRIAL_LANDS_PLOTS = 'INDUSTRIAL_LANDS_PLOTS', _('Industrial Lands/Plots')
        AGRICULTURAL_FARM_LAND = 'AGRICULTURAL_FARM_LAND', _('Agricultural/Farm Land')
        HOTEL_RESORTS = 'HOTEL_RESORTS', _('Hotel/Resorts')
        GUEST_HOUSE_BANQUET_HALLS = 'GUEST_HOUSE_BANQUET_HALLS', _('Guest-House/Banquet-Halls')
        WAREHOUSE = 'WAREHOUSE', _('Ware House')
        COLD_STORAGE = 'COLD_STORAGE', _('Cold Storage')
        FACTORY = 'FACTORY', _('Factory')
        MANUFACTURING = 'MANUFACTURING', _('Manufacturing')
        OTHER_PROPERTY = 'OTHER_PROPERTY', _('Other')
    
    class ProjectType(models.TextChoices):
        RESIDENTIAL = 'RESIDENTIAL', _('Residential')
        COMMERCIAL = 'COMMERCIAL', _('Commercial')
    
    class ConstructionStatus(models.TextChoices):
        UPCOMING = 'UPCOMING', _('Upcoming')
        UNDER_CONSTRUCTION = 'UNDER_CONSTRUCTION', _('Under Construction')
        PHASE_1_COMPLETED = 'PHASE_1_COMPLETED', _('Phase 1 Completed')
        PHASE_2_COMPLETED = 'PHASE_2_COMPLETED', _('Phase 2 Completed')
        LAST_PHASE_PENDING = 'LAST_PHASE_PENDING', _('Last Phase Pending')
        READY_TO_MOVE = 'READY_TO_MOVE', _('Ready to Move')
        PARTIALLY_READY_TO_MOVE = 'PARTIALLY_READY_TO_MOVE', _('Partially Ready to Move')
        NEW_LAUNCH = 'NEW_LAUNCH', _('New Launch')
    
    # Basic Information
    name = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        help_text="Name of the project"
    )
    locality = models.CharField(
        max_length=150,
        null=False,
        blank=False,
        help_text="Locality of the project"
    )
    city = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        help_text="City where the project is located"
    )
    district = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        help_text="District where the project is located"
    )
    state = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        help_text="State where the project is located"
    )
    address = models.TextField(
        blank=True,
        help_text="Full address of the project"
    )
    landmark = models.CharField(
        max_length=150,
        blank=True,
        help_text="Landmark near the project"
    )
    
    # Pricing Information
    price_range_start = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=False,
        blank=False,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Starting price range"
    )
    price_range_end = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=False,
        blank=False,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Ending price range"
    )
    per_sq_ft_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=False,
        blank=False,
        help_text="Price per square foot"
    )
    
    # Area Information
    total_area = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=False,
        blank=False,
        help_text="Total area of the project"
    )
    open_area = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Open area in the project"
    )
    
    # Project Details
    rera_approved = models.BooleanField(
        default=False,
        null=False,
        blank=False,
        help_text="Is the project RERA approved?"
    )
    possession = models.DateField(
        null=False,
        blank=False,
        help_text="Estimated possession date"
    )
    completion_year = models.DateField(
        null=False,
        blank=False,
        help_text="Estimated completion year"
    )
    property_type = models.CharField(
        max_length=30,
        choices=PropertyType.choices,
        null=False,
        blank=False,
        help_text="Type of property"
    )
    project_type = models.CharField(
        max_length=15,
        choices=ProjectType.choices,
        null=False,
        blank=False,
        help_text="Type of project (Residential/Commercial)"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the project"
    )
    advantages = models.TextField(
        blank=True,
        help_text="Advantages of the project"
    )
    disadvantages = models.TextField(
        blank=True,
        help_text="Disadvantages of the project"
    )
    developed_by = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        help_text="Developer of the project"
    )
    construction_status = models.CharField(
        max_length=25,
        choices=ConstructionStatus.choices,
        null=False,
        blank=False,
        help_text="Current construction status"
    )
    negotiable = models.BooleanField(
        default=False,
        null=False,
        blank=False,
        help_text="Is the price negotiable?"
    )
    total_number_of_towers = models.PositiveIntegerField(
        null=False,
        blank=False,
        help_text="Total number of towers in the project"
    )
    total_number_of_floors = models.PositiveIntegerField(
        null=False,
        blank=False,
        help_text="Total number of floors in the project"
    )
    total_rooms = models.PositiveIntegerField(
        null=False,
        blank=False,
        help_text="Total number of rooms in the project"
    )
    
    # Relationships
    highlights = models.ManyToManyField(
        Highlight,
        related_name='projects',
        blank=True,
        help_text="Highlights/features of the project"
    )
    amenities = models.ManyToManyField(
        Amenity,
        related_name='projects',
        blank=True,
        help_text="Amenities available in the project"
    )
    nearby_places = models.ManyToManyField(
        NearbyPlace,
        related_name='projects',
        blank=True,
        help_text="Nearby places to the project"
    )

    active = models.BooleanField(default=True,null=True,blank=True,)    

    # Search
    search_vector = SearchVectorField(null=True, blank=True)
    

    def save(self, *args, **kwargs):
        # Your existing save logic
        super().save(*args, **kwargs)
        
        # Update search vector after save
        if self._state.adding or 'update_fields' not in kwargs:
            self.update_search_vector()

    def update_search_vector(self):
        if isinstance(self, Project):
            self.search_vector = SearchVector('name', weight='A') + \
                            SearchVector('description', weight='B') + \
                            SearchVector('city', weight='B') + \
                            SearchVector('locality', weight='B') + \
                            SearchVector('district', weight='C') + \
                            SearchVector('state', weight='C') + \
                            SearchVector('address', weight='C') + \
                            SearchVector('landmark', weight='D') + \
                            SearchVector('developed_by', weight='D')
            self.save(update_fields=['search_vector'])


    def __str__(self):
        return f"{self.name}, {self.locality}, {self.city}"
    
    def get_absolute_url(self):
        return reverse('admin:key2yourhomeApp_project_change', args=[str(self.id)])
    

    def clean(self):
        if self.price_range_start > self.price_range_end:
            raise ValidationError("Start price cannot be higher than end price")

    
    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        ordering = ['name']
        indexes = [
            GinIndex(fields=['search_vector']),
            models.Index(fields=['search_vector']),
            models.Index(fields=['name']),
            models.Index(fields=['city']),
            models.Index(fields=['state']),
            models.Index(fields=['property_type']),
            models.Index(fields=['project_type']),
            models.Index(fields=['construction_status']),
        ]

class FloorPlan(BaseModel):
    """Model representing floor plans for projects"""
    class NumberOfBedrooms(models.TextChoices):
        ONE_BHK = '1_BHK', _('1 BHK')
        TWO_BHK = '2_BHK', _('2 BHK')
        THREE_BHK = '3_BHK', _('3 BHK')
        FOUR_BHK = '4_BHK', _('4 BHK')
        FIVE_BHK = '5_BHK', _('5 BHK')
        SIX_BHK = '6_BHK', _('6 BHK')
        SEVEN_BHK = '7_BHK', _('7 BHK')
        EIGHT_BHK = '8_BHK', _('8 BHK')
        NINE_BHK = '9_BHK', _('9 BHK')
        MORE_THAN_NINE_BHK = '9+_BHK', _('9+ BHK')
    
    class ConstructionStatus(models.TextChoices):
        UPCOMING = 'UPCOMING', _('Upcoming')
        UNDER_CONSTRUCTION = 'UNDER_CONSTRUCTION', _('Under Construction')
        PHASE_1_COMPLETED = 'PHASE_1_COMPLETED', _('Phase 1 Completed')
        PHASE_2_COMPLETED = 'PHASE_2_COMPLETED', _('Phase 2 Completed')
        LAST_PHASE_PENDING = 'LAST_PHASE_PENDING', _('Last Phase Pending')
        READY_TO_MOVE = 'READY_TO_MOVE', _('Ready to Move')
        PARTIALLY_READY_TO_MOVE = 'PARTIALLY_READY_TO_MOVE', _('Partially Ready to Move')
        NEW_LAUNCH = 'NEW_LAUNCH', _('New Launch')
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='floor_plans',
        null=False,
        blank=False
    )
    carpet_area = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=False,
        blank=False,
        help_text="Carpet area in square feet/meters"
    )
    price_range_start = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=False,
        blank=False,
        help_text="Starting price range for this floor plan"
    )
    price_range_end = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=False,
        blank=False,
        help_text="Ending price range for this floor plan"
    )
    number_of_bedrooms = models.CharField(
        max_length=10,
        choices=NumberOfBedrooms.choices,
        null=False,
        blank=False,
        help_text="Number of bedrooms configuration"
    )
    construction_status = models.CharField(
        max_length=25,
        choices=ConstructionStatus.choices,
        null=True,
        blank=True,
        help_text="Construction status for this floor plan"
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Fixed price (if applicable)"
    )
    possession = models.DateField(
        null=True,
        blank=True,
        help_text="Possession date for this floor plan"
    )
    
    # Area breakdowns
    living_dining_area_length = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Living/Dining area length"
    )
    living_dining_area_breadth = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Living/Dining area breadth"
    )
    kitchen_area_length = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Kitchen area length"
    )
    kitchen_area_breadth = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Kitchen area breadth"
    )
    bedroom_area_length = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Bedroom area length"
    )
    bedroom_area_breadth = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Bedroom area breadth"
    )
    toilet_area_length = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Toilet area length"
    )
    toilet_area_breadth = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Toilet area breadth"
    )
    bathroom_area_length = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Bathroom area length"
    )
    bathroom_area_breadth = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Bathroom area breadth"
    )
    utility_area_length = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Utility area length"
    )
    utility_area_breadth = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Utility area breadth"
    )
    wardrobe_area_length = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Wardrobe area length"
    )
    wardrobe_area_breadth = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Wardrobe area breadth"
    )
    foyer_area_length = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Foyer area length"
    )
    foyer_area_breadth = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Foyer area breadth"
    )
    
    def __str__(self):
        return f"{self.project.name} - {self.get_number_of_bedrooms_display()} - {self.carpet_area} sq.ft"
    def clean(self):
        super().clean()  # always call parent's clean method
        if self.price_range_start is not None and self.price_range_end is not None:
            if self.price_range_start >= self.price_range_end:
                raise ValidationError({
                    "price_range_end": _("Price range end must be greater than price range start.")
                })
    class Meta:
        verbose_name = "Floor Plan"
        verbose_name_plural = "Floor Plans"
        ordering = ['project', 'number_of_bedrooms']
        unique_together = ['project', 'number_of_bedrooms', 'carpet_area']

class RoomPlan(BaseModel):
    """Model representing room plans for projects"""
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='room_plans',
        null=False,
        blank=False
    )
    number_of_bedrooms = models.CharField(
        max_length=10,
        null=False,
        blank=False,
        help_text="Number of bedrooms configuration (e.g., 1BHK, 2BHK)"
    )
    carpet_area = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=False,
        blank=False,
        help_text="Carpet area in square feet/meters"
    )
    price_range_start = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=False,
        blank=False,
        help_text="Starting price range for this room plan"
    )
    price_range_end = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=False,
        blank=False,
        help_text="Ending price range for this room plan"
    )
    
    def __str__(self):
        return f"{self.project.name} - {self.number_of_bedrooms} - {self.carpet_area} sq.ft"
    
    def clean(self):
        if self.price_range_start >= self.price_range_end:
            raise ValidationError(_("Price range end must be greater than price range start"))
    
    class Meta:
        verbose_name = "Room Plan"
        verbose_name_plural = "Room Plans"
        ordering = ['project', 'number_of_bedrooms']
        unique_together = ['project', 'number_of_bedrooms', 'carpet_area']

class Property(BaseModel):
    """Model representing a real estate property"""
    class NumberOfBedrooms(models.TextChoices):
        ONE_BHK = '1_BHK', _('1 BHK')
        TWO_BHK = '2_BHK', _('2 BHK')
        THREE_BHK = '3_BHK', _('3 BHK')
        FOUR_BHK = '4_BHK', _('4 BHK')
        FIVE_BHK = '5_BHK', _('5 BHK')
        SIX_BHK = '6_BHK', _('6 BHK')
        SEVEN_BHK = '7_BHK', _('7 BHK')
        EIGHT_BHK = '8_BHK', _('8 BHK')
        NINE_BHK = '9_BHK', _('9 BHK')
        MORE_THAN_NINE_BHK = '9+_BHK', _('9+ BHK')
    
    class Facing(models.TextChoices):
        EAST = 'EAST', _('East')
        WEST = 'WEST', _('West')
        NORTH = 'NORTH', _('North')
        SOUTH = 'SOUTH', _('South')
    
    class PropertyType(models.TextChoices):
        RESIDENTIAL_APARTMENT = 'RESIDENTIAL_APARTMENT', _('Residential Apartment')
        INDEPENDENT_BUILDER_FLOOR = 'INDEPENDENT_BUILDER_FLOOR', _('Independent/Builder Floor')
        INDEPENDENT_HOUSE_VILLA = 'INDEPENDENT_HOUSE_VILLA', _('Independent House/Villa')
        RESIDENTIAL_LAND = 'RESIDENTIAL_LAND', _('Residential Land')
        STUDIO_APARTMENT = 'STUDIO_APARTMENT', _('1 RK/Studio Apartment')
        FARMHOUSE = 'FARMHOUSE', _('Farmhouse')
        SERVICED_APARTMENTS = 'SERVICED_APARTMENTS', _('Serviced Apartments')
        OTHER = 'OTHER', _('Other')
        OFFICE_SPACES = 'OFFICE_SPACES', _('Office Spaces')
        READY_TO_MOVE = 'READY_TO_MOVE', _('Ready to Move')
        BARESHELL = 'BARESHELL', _('Bare Shell')
        CO_WORKING = 'CO_WORKING', _('Co-Working')
        RETAIL_SHOPS_SHOWROOMS = 'RETAIL_SHOPS_SHOWROOMS', _('Retail Shops/Showrooms')
        SHOPS = 'SHOPS', _('Shops')
        SHOWROOMS = 'SHOWROOMS', _('Showrooms')
        OTHER_COMMERCIAL_SPACES = 'OTHER_COMMERCIAL_SPACES', _('Other Commercial Spaces')
        COMMERCIAL_LAND_INST_LAND = 'COMMERCIAL_LAND_INST_LAND', _('Commercial/Institutional Land')
        INDUSTRIAL_LANDS_PLOTS = 'INDUSTRIAL_LANDS_PLOTS', _('Industrial Lands/Plots')
        AGRICULTURAL_FARM_LAND = 'AGRICULTURAL_FARM_LAND', _('Agricultural/Farm Land')
        HOTEL_RESORTS = 'HOTEL_RESORTS', _('Hotel/Resorts')
        GUEST_HOUSE_BANQUET_HALLS = 'GUEST_HOUSE_BANQUET_HALLS', _('Guest House/Banquet Halls')
        WAREHOUSE = 'WAREHOUSE', _('Warehouse')
        COLD_STORAGE = 'COLD_STORAGE', _('Cold Storage')
        FACTORY = 'FACTORY', _('Factory')
        MANUFACTURING = 'MANUFACTURING', _('Manufacturing')
        OTHER_PROPERTY = 'OTHER_PROPERTY', _('Other')
    
    class ConstructionStatus(models.TextChoices):
        UPCOMING = 'UPCOMING', _('Upcoming')
        UNDER_CONSTRUCTION = 'UNDER_CONSTRUCTION', _('Under Construction')
        PHASE_1_COMPLETED = 'PHASE_1_COMPLETED', _('Phase 1 Completed')
        PHASE_2_COMPLETED = 'PHASE_2_COMPLETED', _('Phase 2 Completed')
        LAST_PHASE_PENDING = 'LAST_PHASE_PENDING', _('Last Phase Pending')
        READY_TO_MOVE = 'READY_TO_MOVE', _('Ready to Move')
        PARTIALLY_READY_TO_MOVE = 'PARTIALLY_READY_TO_MOVE', _('Partially Ready to Move')
        NEW_LAUNCH = 'NEW_LAUNCH', _('New Launch')
    
    class FurnishingStatus(models.TextChoices):
        UNFURNISHED = 'UNFURNISHED', _('Unfurnished')
        SEMI_FURNISHED = 'SEMI_FURNISHED', _('Semi Furnished')
        FURNISHED = 'FURNISHED', _('Furnished')
    
    class OwnershipType(models.TextChoices):
        FREEHOLD = 'FREEHOLD', _('Freehold')
        LEASEHOLD = 'LEASEHOLD', _('Leasehold')
        INDIVIDUAL_OWNERSHIP = 'INDIVIDUAL_OWNERSHIP', _('Individual Ownership')
        CO_OWNERSHIP = 'CO_OWNERSHIP', _('Co-Ownership')
    
    class TransactionType(models.TextChoices):
        RESALE = 'RESALE', _('Resale')
        NEW_PROPERTY = 'NEW_PROPERTY', _('New Property')
    
    class PowerBackup(models.TextChoices):
        FULL = 'FULL', _('Full')
        PARTIAL = 'PARTIAL', _('Partial')
        NONE = 'NONE', _('None')
    
    class WaterSource(models.TextChoices):
        SEVEN_DAY_24_HOURS = '24_7_WATER_SUPPLY', _('24*7 Water Supply')
        MUNICIPAL_CORPORATION = 'MUNICIPAL_CORPORATION', _('Municipal Corporation')
    
    # Location Information
    city = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        help_text="City where the property is located"
    )
    locality = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        help_text="Locality of the project"
    )
    district = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        help_text="District where the property is located"
    )
    state = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        help_text="State where the property is located"
    )
    landmark = models.CharField(
        max_length=100,
        blank=True,
        help_text="Landmark near the property"
    )
    address = models.TextField(
        null=False,
        blank=False,
        help_text="Full address of the property"
    )
    society_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Society name where the property is located"
    )
    
    # Property Details
    floor_no = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Floor number of the property"
    )
    property_age = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MaxValueValidator(100)],
        help_text="Property age in years"
    )
    configuration = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        help_text="Configuration of the property (e.g., 1 Bedroom, 2 Bathrooms)"
    )
    price_in_rs = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=False,
        blank=False,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Price of the property in INR"
    )
    per_sq_ft_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=False,
        blank=False,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Price per square foot of the property in INR"
    )
    carpet_area = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Carpet Area of the Property"
    )
    build_up_area = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Build-up Area of the Property"
    )
    verified = models.BooleanField(
        default=False,
        null=False,
        blank=False,
        help_text="Verification status of the property"
    )
    rera_approved = models.BooleanField(
        default=False,
        null=False,
        blank=False,
        help_text="RERA approval status of the property"
    )
    negotiable = models.BooleanField(
        default=False,
        null=False,
        blank=False,
        help_text="Is the property price negotiable?"
    )
    gated_community = models.BooleanField(
        default=False,
        null=False,
        blank=False,
        help_text="Is the property located in a gated community?"
    )
    corner_property = models.BooleanField(
        null=True,
        blank=True,
        help_text="Is the property located at junctions or corner?"
    )
    pet_friendly = models.BooleanField(
        default=False,
        null=False,
        blank=False,
        help_text="Pet Friendly status of the property"
    )
    number_of_bedrooms = models.CharField(
        max_length=10,
        choices=NumberOfBedrooms.choices,
        null=False,
        blank=False,
        help_text="Number of bedrooms in the property"
    )
    facing = models.CharField(
        max_length=10,
        choices=Facing.choices,
        null=True,
        blank=True,
        help_text="Facing direction of the property"
    )
    property_type = models.CharField(
        max_length=30,
        choices=PropertyType.choices,
        null=False,
        blank=False,
        help_text="Type of property"
    )
    construction_status = models.CharField(
        max_length=25,
        choices=ConstructionStatus.choices,
        null=False,
        blank=False,
        help_text="Construction status of the property"
    )
    furnishing_status = models.CharField(
        max_length=15,
        choices=FurnishingStatus.choices,
        null=False,
        blank=False,
        help_text="Furnishing status of the property"
    )
    ownership_type = models.CharField(
        max_length=20,
        choices=OwnershipType.choices,
        null=False,
        blank=False,
        help_text="Type of ownership of the property"
    )
    transaction_type = models.CharField(
        max_length=15,
        choices=TransactionType.choices,
        null=False,
        blank=False,
        help_text="Transaction type (resale or new property)"
    )
    power_backup = models.CharField(
        max_length=10,
        choices=PowerBackup.choices,
        null=False,
        blank=False,
        help_text="Power backup in the property"
    )
    water_source = models.CharField(
        max_length=25,
        choices=WaterSource.choices,
        null=True,
        blank=True,
        help_text="Water source for the property"
    )
    property_code = models.CharField(
        max_length=50,
        unique=True,
        null=False,
        blank=False,
        default=uuid.uuid4,
        help_text="Unique code for the property"
    )
    width_of_facing_road = models.FloatField(
        null=True,
        blank=True,
        help_text="Width of the road facing the property"
    )
    advantages = models.TextField(
        blank=True,
        help_text="Advantages of the property"
    )
    disadvantages = models.TextField(
        blank=True,
        help_text="Disadvantages of the property"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the property"
    )
    
    # Relationships
    nearby_places = models.ManyToManyField(
        NearbyPlace,
        related_name='properties',
        blank=True,
        help_text="Nearby places to the property"
    )
    flooring = models.ForeignKey(
        Flooring,
        on_delete=models.PROTECT,
        related_name='properties',
        null=False,
        blank=False,
        help_text="Type of flooring in the property"
    )
    parking = models.ForeignKey(
        Parking,
        on_delete=models.PROTECT,
        related_name='properties',
        null=False,
        blank=False,
        help_text="Type of parking available"
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.PROTECT,
        related_name='properties',
        null=False,
        blank=False,
        help_text="Project this property belongs to"
    )
    furnishings = models.ManyToManyField(
        Furnishing,
        related_name='properties',
        blank=True,
        help_text="Furnishings available in the property"
    )
    overlooking = models.ManyToManyField(
        Overlooking,
        related_name='properties',
        blank=True,
        help_text="What the property overlooks"
    )
    highlights = models.ManyToManyField(
        Highlight,
        related_name='properties',
        blank=True,
        help_text="Highlights/features of the property"
    )
    amenities = models.ManyToManyField(
        Amenity,
        related_name='properties',
        blank=True,
        help_text="Amenities available in the property"
    )
    
    active = models.BooleanField(default=True,null=True,blank=True,)   

    # Search
    search_vector = SearchVectorField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.property_code} - {self.property_type} - {self.city}"
    
    def clean(self):
        if self.carpet_area and self.build_up_area and self.carpet_area > self.build_up_area:
            raise ValidationError(_("Carpet area cannot be greater than build-up area"))
    
    def save(self, *args, **kwargs):
        if not self.property_code:
            self.property_code = f"PROP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)
        # Update search vector after save
        if self._state.adding or 'update_fields' not in kwargs:
            self.update_search_vector()

    def update_search_vector(self):
        if isinstance(self, Property):
            self.search_vector = SearchVector('property_code', weight='A') + \
                            SearchVector('description', weight='B') + \
                            SearchVector('city', weight='B') + \
                            SearchVector('locality', weight='B') + \
                            SearchVector('district', weight='C') + \
                            SearchVector('state', weight='C') + \
                            SearchVector('address', weight='C') + \
                            SearchVector('society_name', weight='C') + \
                            SearchVector('landmark', weight='D')
            self.save(update_fields=['search_vector'])
    
    
    class Meta:
        verbose_name = "Property"
        verbose_name_plural = "Properties"
        ordering = ['-created_at']
        indexes = [
            GinIndex(fields=['search_vector']),
            models.Index(fields=['search_vector']),
            models.Index(fields=['city']),
            models.Index(fields=['locality']),
            models.Index(fields=['district']),
            models.Index(fields=['state']),
            models.Index(fields=['property_type']),
            models.Index(fields=['construction_status']),
            models.Index(fields=['furnishing_status']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['price_in_rs']),
            models.Index(fields=['per_sq_ft_price']),
            models.Index(fields=['property_code']),
        ]

class Bookmark(BaseModel):
    """Model representing user bookmarks for properties and projects"""
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='bookmarks',
        null=False,
        blank=False,
        help_text="User who bookmarked the property/project"
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='bookmarks',
        null=True,
        blank=True,
        help_text="Bookmarked property"
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='bookmarks',
        null=True,
        blank=True,
        help_text="Bookmarked project"
    )
    
    def __str__(self):
        if self.property:
            return f"{self.user.username} - {self.property.property_code}"
        return f"{self.user.username} - {self.project.name}"
    
    def clean(self):
        if not self.property and not self.project:
            raise ValidationError(_("Bookmark must be associated with either a property or project"))
        if self.property and self.project:
            raise ValidationError(_("Bookmark can only be associated with either a property or project, not both"))
    
    class Meta:
        verbose_name = "Bookmark"
        verbose_name_plural = "Bookmarks"
        ordering = ['-created_at']
        unique_together = [
            ['user', 'property'],
            ['user', 'project']
        ]

class Review(models.Model):
    """
    Abstract base model for reviews with common fields and methods
    """
    class Rating(models.IntegerChoices):
        POOR = 1, _('1 - Poor')
        FAIR = 2, _('2 - Fair')
        AVERAGE = 3, _('3 - Average')
        GOOD = 4, _('4 - Good')
        EXCELLENT = 5, _('5 - Excellent')

    # Review Metadata
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='%(class)s_reviews',
        verbose_name=_('user'),
        help_text=_("User who submitted the review")
    )
    rating = models.PositiveSmallIntegerField(
        choices=Rating.choices,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_('rating'),
        help_text=_("Rating from 1 (Poor) to 5 (Excellent)")
    )
    title = models.CharField(
        max_length=100,
        verbose_name=_('title'),
        help_text=_("Brief summary of the review")
    )
    comment = models.TextField(
        verbose_name=_('comment'),
        help_text=_("Detailed review content")
    )
    
    # Review Categories (for analytics)
    LOCATION_RATING = 'location'
    DESIGN_RATING = 'design'
    AMENITIES_RATING = 'amenities'
    QUALITY_RATING = 'quality'
    VALUE_RATING = 'value'
    
    CATEGORY_CHOICES = [
        (LOCATION_RATING, _('Location')),
        (DESIGN_RATING, _('Design & Architecture')),
        (AMENITIES_RATING, _('Amenities')),
        (QUALITY_RATING, _('Construction Quality')),
        (VALUE_RATING, _('Value for Money')),
    ]
    
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default=LOCATION_RATING,
        verbose_name=_('review category'),
        help_text=_("Main focus of this review")
    )
    
    # Status Tracking
    is_approved = models.BooleanField(
        default=False,
        verbose_name=_('is approved'),
        help_text=_("Has this review been approved by moderators?")
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name=_('is featured'),
        help_text=_("Should this review be prominently displayed?")
    )
    helpful_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('helpful count'),
        help_text=_("Number of users who found this review helpful")
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        verbose_name=_('created at')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('updated at')
    )
    
    # Response System
    owner_response = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('owner response'),
        help_text=_("Response from the property/project owner")
    )
    response_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('response date')
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']
        verbose_name = _('review')
        verbose_name_plural = _('reviews')
        indexes = [
            models.Index(fields=['rating']),
            models.Index(fields=['is_approved']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.get_rating_display()}"

    @property
    def is_edited(self):
        """Check if review has been edited after creation"""
        if self.updated_at and self.created_at:
            return self.updated_at > self.created_at + timezone.timedelta(minutes=1)
        return False

    @property
    def short_comment(self):
        """Return shortened version of comment for display"""
        return f"{self.comment[:100]}..." if len(self.comment) > 100 else self.comment

    def get_absolute_url(self):
        """Get URL for the review detail view"""
        return reverse(f'review:{self._meta.model_name}_detail', kwargs={'pk': self.pk})

class ProjectReview(Review):
    """
    Review model specifically for Projects with additional analytics
    """
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('project'),
        help_text=_("Project being reviewed")
    )
    
     # Project-specific ratings
    design_rating = models.PositiveSmallIntegerField(
        choices=Review.Rating.choices,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_('design rating'),
        help_text=_("Rating for project design and architecture")
    )
    location_rating = models.PositiveSmallIntegerField(
        choices=Review.Rating.choices,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_('location rating'),
        help_text=_("Rating for project location")
    )
    amenities_rating = models.PositiveSmallIntegerField(
        choices=Review.Rating.choices,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_('amenities rating'),
        help_text=_("Rating for project amenities")
    )
    quality_rating = models.PositiveSmallIntegerField(
        choices=Review.Rating.choices,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_('quality rating'),
        help_text=_("Rating for construction quality")
    )
    value_rating = models.PositiveSmallIntegerField(
        choices=Review.Rating.choices,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_('value rating'),
        help_text=_("Rating for value for money")
    )
   
    class Meta:
        verbose_name = _('project review')
        verbose_name_plural = _('project reviews')
        unique_together = ('project', 'user')
        ordering = ['-is_featured', '-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.project.name} - {self.get_rating_display()}"

    @property
    def average_rating(self):
        """Calculate average of all category ratings"""
        ratings = [
            self.rating,
            self.design_rating,
            self.location_rating,
            self.amenities_rating,
            self.quality_rating,
            self.value_rating
        ]
        return round(sum(ratings) / len(ratings), 1)

    def save(self, *args, **kwargs):
        """Save the review and update project ratings"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Update project rating stats in the background
        from django.core.exceptions import ImproperlyConfigured
        try:
            from django.db import transaction
            
            # Use transaction.on_commit to ensure this runs after successful save
            transaction.on_commit(
                lambda: self.project.update_rating_stats.delay(self.project_id)
            )
        except ImportError:
            # Fallback to synchronous update if Celery isn't configured
            try:
                self.project.update_rating_stats()
            except Exception as e:
                raise ImproperlyConfigured(
                    f"Failed to update project ratings: {str(e)}"
                ) from e

    def delete(self, *args, **kwargs):
        """Handle review deletion and update project ratings"""
        project_id = self.project_id
        super().delete(*args, **kwargs)
        
        try:
            self.project.update_rating_stats.delay(project_id)
        except ImportError:
            try:
                from .models import Project
                project = Project.objects.get(pk=project_id)
                project.update_rating_stats()
            except Exception:
                pass

class PropertyReview(Review):
    """
    Review model specifically for Properties with additional features
    """
    property_link = models.ForeignKey(
        'Property',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('property'),
        help_text=_("Property being reviewed")
    )
    
    # Property-specific ratings
    condition_rating = models.PositiveSmallIntegerField(
        choices=Review.Rating.choices,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_('condition rating'),
        help_text=_("Rating for property condition")
    )
    neighborhood_rating = models.PositiveSmallIntegerField(
        choices=Review.Rating.choices,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_('neighborhood rating'),
        help_text=_("Rating for the neighborhood")
    )
    value_rating = models.PositiveSmallIntegerField(
        choices=Review.Rating.choices,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_('value rating'),
        help_text=_("Rating for value for money")
    )
    
    # Verification flags
    is_verified_tenant = models.BooleanField(
        default=False,
        verbose_name=_('verified tenant'),
        help_text=_("Was this review submitted by a verified tenant?")
    )
    is_verified_owner = models.BooleanField(
        default=False,
        verbose_name=_('verified owner'),
        help_text=_("Was this review submitted by a verified owner?")
    )
    
    # Transaction context
    move_in_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('move in date'),
        help_text=_("When the reviewer moved in (if applicable)")
    )
    move_out_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('move out date'),
        help_text=_("When the reviewer moved out (if applicable)")
    )

    class Meta(Review.Meta):
        verbose_name = _('property review')
        verbose_name_plural = _('property reviews')
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'property_link'],
                name='unique_user_property_review',
                violation_error_message=_("You have already reviewed this property")
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.property_link.property_code} - {self.get_rating_display()}"

    @property
    def average_category_ratings(self):
        """Calculate average of all category ratings"""
        ratings = [
            self.rating,
            self.condition_rating,
            self.neighborhood_rating,
            self.value_rating
        ]
        return sum(ratings) / len(ratings)

    def clean(self):
        """Validate move-in/move-out dates"""
        super().clean()
        if self.move_out_date and self.move_in_date and self.move_out_date < self.move_in_date:
            raise ValidationError(_("Move out date cannot be before move in date"))

    def save(self, *args, **kwargs):
        """Update property's overall rating when review is saved"""
        super().save(*args, **kwargs)
        self.property_link.update_rating_stats()


