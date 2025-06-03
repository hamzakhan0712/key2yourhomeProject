from pyexpat.errors import messages
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from grappelli.forms import GrappelliSortableHiddenMixin
from .models import (
    User, UserSession, PasswordChangeHistory, SearchQueryLog, SearchSuggestion,
    CookieConsent, Flooring, Parking, Amenity, Highlight, NearbyPlace,
    Overlooking, Furnishing, Media, Phase, Project, FloorPlan, RoomPlan,
    Property, Bookmark, ProjectReview, PropertyReview
)

# Common admin classes
class BaseAdmin(admin.ModelAdmin):
    """Base admin class with common settings"""
    list_per_page = 50
    save_on_top = True
    show_full_result_count = False
    date_hierarchy = 'created_at'


class SortableAdmin(GrappelliSortableHiddenMixin, admin.ModelAdmin):
    """Admin class for sortable models"""
    sortable = 'position'


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'phone', 'is_staff', 'email_verified', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'email_verified', 'is_active', 'last_login')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)
    readonly_fields = ('last_login', 'date_joined', 'verification_token')  # Fields that shouldn't be edited
    list_editable = ('is_active', 'email_verified')  # Fields editable directly from list view
    
    # Explicitly define fieldsets to show all fields
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        (_('Personal Info'), {
            'fields': ('first_name', 'last_name', 'phone', 'profile_picture'),
            'classes': ('grp-collapse grp-open',)
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('grp-collapse grp-closed',)
        }),
        (_('Important Dates'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('grp-collapse grp-closed',)
        }),
        (_('Verification'), {
            'fields': ('email_verified', 'verification_token', 'last_password_change'),
            'classes': ('grp-collapse grp-closed',)
        }),
        (_('Password Reset'), {
            'fields': ('password_reset_token', 'password_reset_expires'),
            'classes': ('grp-collapse grp-closed',)
        }),
    )
    
    # Add this to show all fields in add/edit forms
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    
    # For Grappelli autocomplete lookups
    related_lookup_fields = {
        'fk': ['groups'],
        'm2m': ['user_permissions']
    }

    # Detailed control over what appears in add/edit forms
    def get_fieldsets(self, request, obj=None):
        if not obj:  # This is the add form
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

@admin.register(UserSession)
class UserSessionAdmin(BaseAdmin):
    list_display = ('user', 'ip_address', 'created_at', 'last_activity', 'is_active')
    list_filter = ('is_active', 'remember_me', 'created_at')
    search_fields = ('user__email', 'ip_address', 'user_agent')
    raw_id_fields = ('user',)
    readonly_fields = ('session_key', 'created_at', 'last_activity')


@admin.register(PasswordChangeHistory)
class PasswordChangeHistoryAdmin(BaseAdmin):
    list_display = ('user', 'changed_at')
    search_fields = ('user__email',)
    raw_id_fields = ('user',)
    readonly_fields = ('changed_at',)


@admin.register(SearchQueryLog)
class SearchQueryLogAdmin(BaseAdmin):
    list_display = ('user', 'search_type', 'results_count', 'created_at')
    list_filter = ('search_type', 'created_at')
    search_fields = ('user__email', 'query')
    raw_id_fields = ('user',)
    readonly_fields = ('created_at',)


@admin.register(SearchSuggestion)
class SearchSuggestionAdmin(BaseAdmin):
    list_display = ('term', 'search_type', 'weight', 'use_count', 'last_used')
    list_filter = ('search_type',)
    search_fields = ('term',)
    list_editable = ('weight',)


@admin.register(CookieConsent)
class CookieConsentAdmin(BaseAdmin):
    list_display = ('user', 'session_key', 'consent_date')
    search_fields = ('user__email', 'session_key')
    raw_id_fields = ('user',)
    readonly_fields = ('consent_date',)


# Property Features Admin
class FeatureAdmin(BaseAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Flooring)
class FlooringAdmin(FeatureAdmin):
    pass


@admin.register(Parking)
class ParkingAdmin(BaseAdmin):
    list_display = ('type',)
    search_fields = ('type',)


@admin.register(Amenity)
class AmenityAdmin(FeatureAdmin):
    pass


@admin.register(Highlight)
class HighlightAdmin(FeatureAdmin):
    pass


@admin.register(NearbyPlace)
class NearbyPlaceAdmin(BaseAdmin):
    list_display = ('name', 'distance')
    search_fields = ('name',)


@admin.register(Overlooking)
class OverlookingAdmin(FeatureAdmin):
    pass


@admin.register(Furnishing)
class FurnishingAdmin(BaseAdmin):
    list_display = ('name', 'quantity')
    list_editable = ('quantity',)


# Media Admin
class MediaInline(GrappelliSortableHiddenMixin, admin.TabularInline):
    model = Media
    extra = 1
    sortable_field_name = "id"
    classes = ('grp-collapse grp-open',)
    fields = ('title', 'media_type', 'file', 'about')
    raw_id_fields = ('property', 'project')


@admin.register(Media)
class MediaAdmin(BaseAdmin):
    list_display = ('title', 'media_type', 'property', 'project')
    list_filter = ('media_type',)
    search_fields = ('title', 'property__property_code', 'project__name')
    raw_id_fields = ('property', 'project')
    autocomplete_lookup_fields = {
        'fk': ['property', 'project']
    }


# Project Admin
class PhaseInline(admin.TabularInline):
    model = Phase
    extra = 1
    classes = ('grp-collapse grp-closed',)
    fields = ('phase_name', 'number_of_towers', 'construction_status', 'possession', 'completion_year')


class FloorPlanInline(admin.TabularInline):
    model = FloorPlan
    extra = 1
    classes = ('grp-collapse grp-closed',)
    fields = ('number_of_bedrooms', 'carpet_area', 'price_range_start', 'price_range_end', 'construction_status')


class RoomPlanInline(admin.TabularInline):
    model = RoomPlan
    extra = 1
    classes = ('grp-collapse grp-closed',)
    fields = ('number_of_bedrooms', 'carpet_area', 'price_range_start', 'price_range_end')


@admin.register(Project)
class ProjectAdmin(BaseAdmin):
    list_display = ('name', 'locality', 'city', 'property_type', 'construction_status', 'rera_approved', 'active')
    list_filter = ('property_type', 'project_type', 'construction_status', 'rera_approved', 'city', 'state', 'active')
    search_fields = ('name', 'locality', 'city', 'description')
    filter_horizontal = ('highlights', 'amenities', 'nearby_places')
    raw_id_fields = ('nearby_places',)
    readonly_fields = ('search_vector',)
    inlines = [PhaseInline, FloorPlanInline, RoomPlanInline]
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'locality', 'city', 'district', 'state', 'address', 'landmark', 'active'),
            'classes': ('grp-collapse grp-open',)
        }),
        (_('Pricing'), {
            'fields': ('price_range_start', 'price_range_end', 'per_sq_ft_price', 'negotiable'),
            'classes': ('grp-collapse grp-open',)
        }),
        (_('Area Information'), {
            'fields': ('total_area', 'open_area'),
            'classes': ('grp-collapse grp-closed',)
        }),
        (_('Project Details'), {
            'fields': (
                'property_type', 'project_type', 'description', 'advantages', 'disadvantages',
                'developed_by', 'construction_status', 'rera_approved', 'possession',
                'completion_year', 'total_number_of_towers', 'total_number_of_floors', 'total_rooms'
            ),
            'classes': ('grp-collapse grp-closed',)
        }),
        (_('Features'), {
            'fields': ('highlights', 'amenities', 'nearby_places'),
            'classes': ('grp-collapse grp-closed',)
        }),
        (_('Search'), {
            'fields': ('search_vector',),
            'classes': ('grp-collapse grp-closed',)
        }),
    )
    
    related_lookup_fields = {
        'm2m': ['highlights', 'amenities', 'nearby_places']
    }
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('highlights', 'amenities', 'nearby_places')

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        try:
            return super().changeform_view(request, object_id, form_url, extra_context)
        except Exception as e:
            messages.error(request, f"Validation error: {str(e)}")
            return super().changeform_view(request, object_id, form_url, extra_context)

@admin.register(Phase)
class PhaseAdmin(BaseAdmin):
    list_display = ('project', 'phase_name', 'construction_status', 'possession')
    list_filter = ('construction_status', 'number_of_bedrooms')
    search_fields = ('project__name', 'phase_name')
    raw_id_fields = ('project',)
    autocomplete_lookup_fields = {
        'fk': ['project']
    }


@admin.register(FloorPlan)
class FloorPlanAdmin(BaseAdmin):
    list_display = ('project', 'number_of_bedrooms', 'carpet_area', 'price_range_start', 'price_range_end')
    list_filter = ('number_of_bedrooms', 'construction_status')
    search_fields = ('project__name',)
    raw_id_fields = ('project',)
    autocomplete_lookup_fields = {
        'fk': ['project']
    }


@admin.register(RoomPlan)
class RoomPlanAdmin(BaseAdmin):
    list_display = ('project', 'number_of_bedrooms', 'carpet_area', 'price_range_start', 'price_range_end')
    list_filter = ('number_of_bedrooms',)
    search_fields = ('project__name',)
    raw_id_fields = ('project',)
    autocomplete_lookup_fields = {
        'fk': ['project']
    }


# Property Admin
class BookmarkInline(admin.TabularInline):
    model = Bookmark
    extra = 0
    classes = ('grp-collapse grp-closed',)
    raw_id_fields = ('user', 'property', 'project')
    readonly_fields = ('created_at',)


@admin.register(Property)
class PropertyAdmin(BaseAdmin):
    list_display = (
        'property_code', 'property_type', 'city', 'locality', 'price_in_rs', 
        'per_sq_ft_price', 'verified', 'rera_approved', 'active'
    )
    list_filter = (
        'property_type', 'construction_status', 'furnishing_status', 
        'ownership_type', 'transaction_type', 'city', 'state', 
        'verified', 'rera_approved', 'gated_community', 'active'
    )
    search_fields = (
        'property_code', 'city', 'locality', 'district', 'state', 
        'address', 'description'
    )
    filter_horizontal = (
        'nearby_places', 'furnishings', 'overlooking', 'highlights', 'amenities'
    )
    raw_id_fields = ('project', 'flooring', 'parking')
    readonly_fields = ('property_code', 'search_vector', 'created_at', 'updated_at')
    inlines = [MediaInline, BookmarkInline]
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'property_code', 'property_type', 'construction_status', 
                'furnishing_status', 'ownership_type', 'transaction_type', 'active'
            ),
            'classes': ('grp-collapse grp-open',)
        }),
        (_('Location'), {
            'fields': (
                'city', 'locality', 'district', 'state', 'landmark', 
                'address', 'society_name'
            ),
            'classes': ('grp-collapse grp-open',)
        }),
        (_('Details'), {
            'fields': (
                'floor_no', 'property_age', 'configuration', 'facing', 
                'carpet_area', 'build_up_area', 'width_of_facing_road'
            ),
            'classes': ('grp-collapse grp-closed',)
        }),
        (_('Pricing'), {
            'fields': ('price_in_rs', 'per_sq_ft_price', 'negotiable'),
            'classes': ('grp-collapse grp-closed',)
        }),
        (_('Features'), {
            'fields': (
                'flooring', 'parking', 'furnishings', 'overlooking', 
                'highlights', 'amenities', 'nearby_places'
            ),
            'classes': ('grp-collapse grp-closed',)
        }),
        (_('Utilities'), {
            'fields': ('power_backup', 'water_source'),
            'classes': ('grp-collapse grp-closed',)
        }),
        (_('Flags'), {
            'fields': (
                'verified', 'rera_approved', 'gated_community', 
                'corner_property', 'pet_friendly'
            ),
            'classes': ('grp-collapse grp-closed',)
        }),
        (_('Description'), {
            'fields': ('description', 'advantages', 'disadvantages'),
            'classes': ('grp-collapse grp-closed',)
        }),
        (_('Project'), {
            'fields': ('project',),
            'classes': ('grp-collapse grp-closed',)
        }),
        (_('Search'), {
            'fields': ('search_vector',),
            'classes': ('grp-collapse grp-closed',)
        }),
    )
    
    related_lookup_fields = {
        'fk': ['project', 'flooring', 'parking'],
        'm2m': ['furnishings', 'overlooking', 'highlights', 'amenities', 'nearby_places']
    }
    
    autocomplete_lookup_fields = {
        'fk': ['project', 'flooring', 'parking'],
        'm2m': ['furnishings', 'overlooking', 'highlights', 'amenities', 'nearby_places']
    }
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'project', 'flooring', 'parking'
        ).prefetch_related(
            'furnishings', 'overlooking', 'highlights', 'amenities', 'nearby_places'
        )


@admin.register(Bookmark)
class BookmarkAdmin(BaseAdmin):
    list_display = ('user', 'property', 'project', 'created_at')
    search_fields = ('user__email', 'property__property_code', 'project__name')
    raw_id_fields = ('user', 'property', 'project')
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'property', 'project')


# Review Admin
class ReviewAdmin(BaseAdmin):
    list_display = ('user', 'rating', 'title', 'is_approved', 'is_featured', 'created_at')
    list_filter = ('rating', 'is_approved', 'is_featured', 'created_at')
    search_fields = ('user__email', 'title', 'comment')
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at', 'helpful_count')
    list_editable = ('is_approved', 'is_featured')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'rating', 'title', 'comment', 'category')
        }),
        (_('Status'), {
            'fields': ('is_approved', 'is_featured', 'helpful_count'),
            'classes': ('grp-collapse grp-closed',)
        }),
        (_('Response'), {
            'fields': ('owner_response', 'response_date'),
            'classes': ('grp-collapse grp-closed',)
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('grp-collapse grp-closed',)
        }),
    )


@admin.register(ProjectReview)
class ProjectReviewAdmin(ReviewAdmin):
    list_display = ('user', 'project', 'rating', 'title', 'is_approved', 'is_featured')
    raw_id_fields = ('user', 'project')
    autocomplete_lookup_fields = {
        'fk': ['project']
    }
    
    fieldsets = ReviewAdmin.fieldsets[0:1] + (
        (_('Project Ratings'), {
            'fields': (
                'project', 'design_rating', 'location_rating', 
                'amenities_rating', 'quality_rating', 'value_rating'
            ),
            'classes': ('grp-collapse grp-open',)
        }),
    ) + ReviewAdmin.fieldsets[1:]


@admin.register(PropertyReview)
class PropertyReviewAdmin(ReviewAdmin):
    list_display = ('user', 'property_link', 'rating', 'title', 'is_approved', 'is_featured')
    raw_id_fields = ('user', 'property_link')
    autocomplete_lookup_fields = {
        'fk': ['property_link']
    }
    
    fieldsets = ReviewAdmin.fieldsets[0:1] + (
        (_('Property Ratings'), {
            'fields': (
                'property_link', 'condition_rating', 'neighborhood_rating', 'value_rating'
            ),
            'classes': ('grp-collapse grp-open',)
        }),
        (_('Verification'), {
            'fields': ('is_verified_tenant', 'is_verified_owner'),
            'classes': ('grp-collapse grp-closed',)
        }),
        (_('Dates'), {
            'fields': ('move_in_date', 'move_out_date'),
            'classes': ('grp-collapse grp-closed',)
        }),
    ) + ReviewAdmin.fieldsets[1:]


# Admin Site Customization
admin.site.site_header = "Key2YourHome Administration"
admin.site.site_title = "Key2YourHome Admin Portal"
admin.site.index_title = "Welcome to Key2YourHome Admin"

# Change list templates for better filtering
admin.site.change_list_template = "auth/change_list_filter_sidebar.html"


