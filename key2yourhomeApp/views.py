
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import uuid
import logging
from django.views.decorators.http import require_POST
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.conf import settings
from django.views.decorators.csrf import ensure_csrf_cookie
from .forms import *
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView
from django.views.decorators.http import require_GET
from decimal import Decimal, InvalidOperation
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail, BadHeaderError
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.translation import gettext_lazy as _
from django.db.models import Value, CharField
from django.db.models.functions import Concat
from user_agents import parse 
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import (
    Case, When, Value, CharField, IntegerField, Q
)
from django.db.models.functions import Concat

logger = logging.getLogger(__name__)

@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.user.is_authenticated:
        return redirect('landing_page')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Send verification email
            try:
                user.send_verification_email()
                messages.success(request, 'Registration successful! Please check your email to verify your account.')
            except Exception as e:
                logger.error(f"Failed to send verification email: {e}")
                messages.warning(request, 'Account created but verification email failed to send. Please contact support.')
            
            return redirect('login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'auth/register.html', {'form': form})

@require_http_methods(["GET", "POST"])
@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        return redirect('landing_page')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # Create session if it doesn't exist
            if not request.session.session_key:
                request.session.create()
            
            # Track user session
            UserSession.objects.create(
                user=user,
                session_key=request.session.session_key,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                remember_me=form.cleaned_data.get('remember', False)
            )
            
            # Perform login
            login(request, user)
            
            # Handle "Remember Me" functionality
            if form.cleaned_data.get('remember'):
                # Set session to expire after SESSION_COOKIE_AGE
                request.session.set_expiry(settings.SESSION_COOKIE_AGE)
            else:
                # Session expires when browser closes
                request.session.set_expiry(0)
            
            messages.success(request, f'Welcome back, {user.first_name}!')
            
            next_url = request.GET.get('next', 'landing_page')
            return redirect(next_url)
    else:
        form = UserLoginForm()
    
    return render(request, 'auth/login.html', {
        'form': form,
        'next': request.GET.get('next', '')
    })

@login_required
@require_http_methods(["GET", "POST"])  # Allow both GET and POST
def logout_view(request):
    # Mark session as inactive
    UserSession.objects.filter(
        user=request.user,
        session_key=request.session.session_key
    ).update(is_active=False)
    
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('landing_page')

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    # Get active sessions with enhanced device detection
    active_sessions = UserSession.objects.filter(
        user=request.user,
        is_active=True
    ).order_by('-last_activity')
    
    # Annotate sessions with device type
    for session in active_sessions:
        user_agent = session.user_agent or ''
        if "Windows" in user_agent:
            session.device_type = "Windows"
            session.device_icon = "windows"
        elif "Mac" in user_agent:
            session.device_type = "MacOS"
            session.device_icon = "mac"
        elif "iPhone" in user_agent:
            session.device_type = "iPhone"
            session.device_icon = "iphone"
        elif "Android" in user_agent:
            session.device_type = "Android"
            session.device_icon = "android"
        else:
            session.device_type = "Unknown Device"
            session.device_icon = "unknown"
    
    # Get bookmarked items with prefetched media
    bookmarks = Bookmark.objects.filter(
        user=request.user
    ).select_related(
        'property', 
        'project'
    ).prefetch_related(
        'property__media',
        'project__media'
    ).order_by('-created_at')
    
    return render(request, 'auth/profile.html', {
        'form': form,
        'active_sessions': active_sessions,
        'bookmarks': bookmarks,
        'current_session_key': request.session.session_key
    })

@login_required
@require_POST
def delete_profile_view(request):
    user = request.user
    email = user.email
    
    # Send confirmation email before deletion
    subject = 'Account Deletion Confirmation'
    html_message = render_to_string('auth/account_deleted.html', {
        'user': user,
        'site_name': settings.SITE_NAME,
        'support_email': settings.SUPPORT_EMAIL,
    })
    plain_message = strip_tags(html_message)
    
    try:
        # Delete the user account
        user.delete()
        
        # Logout the user
        logout(request)
        
        # Send confirmation email
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            html_message=html_message,
            fail_silently=False
        )
        
        messages.success(request, 'Your account has been permanently deleted. We\'re sorry to see you go.')
        return redirect('landing_page')
    
    except Exception as e:
        logger.error(f"Error deleting account for {email}: {str(e)}")
        messages.error(request, 'An error occurred while deleting your account. Please contact support.')
        return redirect('profile')

@login_required
@require_POST
def terminate_session_view(request, session_id):
    try:
        session = UserSession.objects.get(
            id=session_id,
            user=request.user,
            is_active=True
        )
        if session.session_key == request.session.session_key:
            messages.error(request, 'You cannot terminate your current session.')
        else:
            session.is_active = False
            session.save()
            messages.success(request, 'Session terminated successfully.')
    except UserSession.DoesNotExist:
        messages.error(request, 'Session not found or already terminated.')
    
    return redirect('profile')

@login_required
@require_http_methods(["GET", "POST"])
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            try:
                # Validate new password against common patterns
                new_password = form.cleaned_data['new_password1']
                validate_password(new_password, user=request.user)
                
                # Check against previous passwords
                if PasswordChangeHistory.objects.filter(
                    user=request.user,
                    password=request.user.password
                ).exists():
                    messages.error(request, 'You cannot reuse a previous password.')
                    return redirect('change_password')
                
                user = form.save()
                update_session_auth_hash(request, user)
                
                # Log password change
                PasswordChangeHistory.objects.create(
                    user=user,
                    password=user.password,
                    changed_at=timezone.now()
                )
                
                user.last_password_change = timezone.now()
                user.save()
                
                # Send email notification
                send_password_change_email(request, user)
                
                messages.success(request, 'Your password was successfully updated!')
                return redirect('profile')
                
            except ValidationError as e:
                for error in e.messages:
                    messages.error(request, error)
    else:
        form = PasswordChangeForm(request.user)
    
    context = {
        'form': form,
        'password_policy': {
            'min_length': 8,
            'require_upper': True,
            'require_lower': True,
            'require_number': True,
            'require_special': True,
        }
    }
    return render(request, 'auth/change_password.html', context)

def send_password_change_email(request, user):
    subject = 'Password Changed Successfully'
    html_message = render_to_string('auth/password_changed.html', {
        'user': user,
        'support_email': settings.SUPPORT_EMAIL,
        'ip_address': get_client_ip(request),
        'site_name': settings.SITE_NAME,
        'logo_url': settings.LOGO_URL,  # Option
    })
    plain_message = strip_tags(html_message)
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False
    )

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@require_http_methods(["GET", "POST"])
def forgot_password_view(request):
    if request.user.is_authenticated:
        return redirect('landing_page')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            token = get_random_string(50)
            user.password_reset_token = token
            user.password_reset_expires = timezone.now() + timezone.timedelta(hours=1)
            user.save()
            
            reset_url = request.build_absolute_uri(
                reverse('reset_password', kwargs={'token': token})
            )
            
            subject = 'Password Reset Request'
            html_message = render_to_string('auth/password_reset.html', {
                'user': user,
                'reset_url': reset_url,
                'expiry_hours': 1,
                'site_name': settings.SITE_NAME,
                'support_email': settings.SUPPORT_EMAIL,
            })
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=False
            )
            
            messages.success(request, 'Password reset link has been sent to your email. It will expire in 1 hour.')
            return redirect('login')
            
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
        except Exception as e:
            logger.error(f"Error sending password reset email: {str(e)}")
            messages.error(request, 'An error occurred while sending the reset link. Please try again later.')
    
    return render(request, 'auth/forgot_password.html')

@require_http_methods(["GET", "POST"])
def reset_password_view(request, token):
    if request.user.is_authenticated:
        return redirect('landing_page')
    
    try:
        user = User.objects.get(
            password_reset_token=token,
            password_reset_expires__gt=timezone.now()
        )
    except User.DoesNotExist:
        messages.error(request, 'Invalid or expired password reset link.')
        return redirect('forgot_password')
    
    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            try:
                new_password = form.cleaned_data['new_password1']
                validate_password(new_password, user=user)
                
                form.save()
                user.password_reset_token = None
                user.password_reset_expires = None
                user.last_password_change = timezone.now()
                user.save()
                
                # Log password change
                PasswordChangeHistory.objects.create(
                    user=user,
                    password=user.password,
                    changed_at=timezone.now()
                )
                
                messages.success(request, 'Your password has been reset successfully. Please login with your new password.')
                return redirect('login')
                
            except ValidationError as e:
                for error in e.messages:
                    messages.error(request, error)
    else:
        form = SetPasswordForm(user)
    
    context = {
        'form': form,
        'token': token,
        'password_policy': {
            'min_length': 8,
            'require_upper': True,
            'require_lower': True,
            'require_number': True,
            'require_special': True,
        }
    }
    return render(request, 'auth/reset_password.html', context)



def landing_page(request):
    # Property type choices
    property_type_choices = Property.PropertyType.choices
    project_status_choices = Project.ConstructionStatus.choices
    bedroom_choices = Property.NumberOfBedrooms.choices
    
    # Get all amenities
    amenities = Amenity.objects.all()
    
    context = {
        'property_type_choices': property_type_choices,
        'project_status_choices': project_status_choices,
        'bedroom_choices': bedroom_choices,
        'amenities': amenities,
    }
    
    return render(request, 'landing/landing.html', context)

def about(request):
    return render(request, 'landing/about.html')


def contact_us(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Basic validation
        if not name or not email or not message:
            messages.error(request, "Please fill in all required fields.")
            return redirect('contact_us')
        
        # Prepare email content
        email_subject = f"New Contact Form Submission: {subject}"
        email_body = f"""
        Name: {name}
        Email: {email}
        Phone: {phone if phone else 'Not provided'}
        Subject: {subject}
        
        Message:
        {message}
        """
        
        try:
            # Send email to admin
            send_mail(
                subject=email_subject,
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['initcore25@gmail.com'],   # Add to settings.py
                fail_silently=False,
            )
            
            # Optional: Send confirmation to user
            send_mail(
                subject="Thank you for contacting us",
                message=f"Dear {name},\n\nWe've received your message and will get back to you soon.\n\nBest regards,\nKey2yourhome Team",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
            
            messages.success(request, "Your message has been sent successfully!")
            return redirect('contact_us')
            
        except BadHeaderError:
            messages.error(request, "Invalid header found.")
            return redirect('contact_us')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('contact_us')
    
    return render(request, 'landing/contact_us.html')


def privacy_policy(request):
    return render(request, 'landing/privacy_policy.html')


def terms_conditions(request):
    return render(request, 'landing/terms_conditions.html')

def faqs(request):
    return render(request, 'landing/faqs.html')


def project_list(request):
    # Initialize filter parameters with safe defaults
    filter_params = {
        'project_type': request.GET.get('project_type', ''),
        'developer': request.GET.get('developer', ''),
        'city': request.GET.get('city', ''),
        'locality': request.GET.get('locality', ''),
        'launch_date_start': request.GET.get('launch_date_start', ''),
        'launch_date_end': request.GET.get('launch_date_end', ''),
        'min_price': request.GET.get('min_price', ''),
        'max_price': request.GET.get('max_price', ''),
        'price_range': request.GET.get('price_range', '50000000'),  # Default 50L
        'min_area': request.GET.get('min_area', ''),
        'max_area': request.GET.get('max_area', ''),
        'amenities': request.GET.getlist('amenities', []),
        'min_rating': request.GET.get('min_rating', ''),
        'per_page': request.GET.get('per_page', '12'),
    }

    # Start with base queryset
    projects = Project.objects.all().order_by('-created_at')
    

    # Apply filters with proper type conversion and validation
    if filter_params['project_type']:
        projects = projects.filter(project_type=filter_params['project_type'])

    if filter_params['developer']:
        projects = projects.filter(developed_by__iexact=filter_params['developer'])

    if filter_params['city']:
        projects = projects.filter(city__iexact=filter_params['city'])

    if filter_params['locality']:
        projects = projects.filter(locality__icontains=filter_params['locality'])

    print("ASDASDASDASD",projects)

    # Date range filter
    try:
        if filter_params['launch_date_start']:
            start_date = datetime.strptime(filter_params['launch_date_start'], '%Y-%m-%d').date()
            projects = projects.filter(launch_date__gte=start_date)
        if filter_params['launch_date_end']:
            end_date = datetime.strptime(filter_params['launch_date_end'], '%Y-%m-%d').date()
            projects = projects.filter(launch_date__lte=end_date)
    except (ValueError, TypeError):
        pass  # Invalid dates are ignored


    

      # Price filters (combine slider and manual inputs)
    price_filters = Q()
    has_price_filter = False
    
    # Check if any price filter is set
    if (filter_params['price_range'] and filter_params['price_range'] != '50000000') or \
       filter_params['min_price'] or filter_params['max_price']:
        has_price_filter = True
        
        try:
            if filter_params['price_range'] and filter_params['price_range'] != '50000000':
                price_value = Decimal(filter_params['price_range'])
                price_filters |= Q(price_range_start__lte=price_value) & Q(price_range_end__gte=price_value)
        except (InvalidOperation, TypeError):
            pass

        try:
            if filter_params['min_price']:
                min_price = Decimal(filter_params['min_price'])
                price_filters &= Q(price_range_end__gte=min_price)
            if filter_params['max_price']:
                max_price = Decimal(filter_params['max_price'])
                price_filters &= Q(price_range_start__lte=max_price)
        except (InvalidOperation, TypeError):
            pass

    if has_price_filter and price_filters:
        projects = projects.filter(price_filters)

    print("ASDASDASDASD 3",projects)

    # Area filters
    area_filters = Q()
    try:
        if filter_params['min_area']:
            min_area = Decimal(filter_params['min_area'])
            area_filters &= Q(total_area__gte=min_area)
        if filter_params['max_area']:
            max_area = Decimal(filter_params['max_area'])
            area_filters &= Q(total_area__lte=max_area)
    except (InvalidOperation, TypeError):
        pass

    if area_filters:
        projects = projects.filter(area_filters)


    
    # Amenities filter (with distinct to avoid duplicates)
    if filter_params['amenities']:
        try:
            amenity_ids = [int(a) for a in filter_params['amenities'] if a.isdigit()]
            if amenity_ids:
                projects = projects.filter(amenities__id__in=amenity_ids).distinct()
        except (ValueError, TypeError):
            pass

    
    

    # Rating filter
    try:
        if filter_params['min_rating']:
            min_rating = Decimal(filter_params['min_rating'])
            projects = projects.filter(rating__gte=min_rating)
    except (InvalidOperation, TypeError):
        pass

    # Get distinct values for filter options (optimized queries)
    filter_options = {
        'cities': Project.objects.values_list('city', flat=True)
                       .distinct().order_by('city'),
        'developers': Project.objects.values_list('developed_by', flat=True)
                         .distinct().order_by('developed_by'),
        'amenities': Amenity.objects.all().order_by('name'),
        'project_types': Project.ProjectType.choices,
    }

    # Pagination with error handling
    try:
        per_page = int(filter_params['per_page'])
        per_page = max(1, min(per_page, 100))  # Enforce reasonable limits
    except (ValueError, TypeError):
        per_page = 12

    paginator = Paginator(projects, per_page)
    page_number = request.GET.get('page', 1)

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    

    # Prepare context
    context = {
        'projects': page_obj,
        'selected_filters': filter_params,
        'selected_amenities': [int(a) for a in filter_params['amenities'] if a.isdigit()],
        **filter_options
    }

    return render(request, 'project/project_list.html', context)


def project_detail(request, pk):
    project = get_object_or_404(Project.objects.prefetch_related(
        'media',
        'highlights',
        'amenities',
        'nearby_places',
        'floor_plans',
        'reviews__user'
    ), pk=pk)

    reviews = project.reviews.filter(is_approved=True)
    total_reviews = reviews.count()

    # Calculate average and category-wise ratings
    if total_reviews:
        avg_rating = round(reviews.aggregate(Avg('rating'))['rating__avg'], 1)

        rating_distribution = {
            stars: reviews.filter(rating=stars).count() for stars in range(5, 0, -1)
        }

        category_ratings = {
            'design': round(reviews.aggregate(Avg('design_rating'))['design_rating__avg'] or 0, 1),
            'location': round(reviews.aggregate(Avg('location_rating'))['location_rating__avg'] or 0, 1),
            'amenities': round(reviews.aggregate(Avg('amenities_rating'))['amenities_rating__avg'] or 0, 1),
            'quality': round(reviews.aggregate(Avg('quality_rating'))['quality_rating__avg'] or 0, 1),
            'value': round(reviews.aggregate(Avg('value_rating'))['value_rating__avg'] or 0, 1),
        }
    else:
        avg_rating = 0
        rating_distribution = {i: 0 for i in range(5, 0, -1)}
        category_ratings = {}

    # Similar projects suggestion
    similar_projects = Project.objects.filter(
        Q(city=project.city) |
        Q(property_type=project.property_type) |
        Q(project_type=project.project_type),
        ~Q(pk=project.pk)
    ).distinct().order_by('-created_at')[:6]

    user_has_reviewed = False
    user_can_review = False
    review_form = None

    if request.user.is_authenticated:
        user_has_reviewed = reviews.filter(user=request.user).exists()
        user_can_review = not user_has_reviewed

        if request.method == 'POST' and user_can_review:
            review_form = ProjectReviewForm(request.POST)
            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.user = request.user
                review.project = project
                review.is_approved = False

                # Determine main category from max sub-rating
                ratings = {
                    'design': review.design_rating,
                    'location': review.location_rating,
                    'amenities': review.amenities_rating,
                    'quality': review.quality_rating,
                    'value': review.value_rating
                }

                review.category = max(ratings, key=ratings.get)

                try:
                    review.save()
                    project.update_rating_stats()
                    messages.success(request, _('Thank you for your review! It will be visible after approval.'))

                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({
                            'status': 'success',
                            'message': 'Review submitted successfully!',
                            'redirect_url': request.path,
                        })
                    return redirect('project_detail', pk=pk)

                except Exception as e:
                    messages.error(request, _('Something went wrong. Please try again later.'))
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({
                            'status': 'error',
                            'message': str(e),
                        }, status=500)
            else:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Please correct the errors below.',
                        'errors': review_form.errors.get_json_data(),
                    }, status=400)
        else:
            review_form = ProjectReviewForm()
        
       

    context = {
        'project': project,
        'reviews': reviews.order_by('-is_featured', '-created_at'),
        'avg_rating': avg_rating,
        'total_reviews': total_reviews,
        'rating_distribution': rating_distribution,
        'category_ratings': category_ratings,
        'review_form': review_form,
        'user_has_reviewed': user_has_reviewed,
        'user_can_review': user_can_review,
        'similar_projects': similar_projects,
    }

    return render(request, 'project/project_detail.html', context)


@login_required
@require_POST
def toggle_project_bookmark(request, project_id):
    try:
        project = Project.objects.get(pk=project_id)
        bookmark, created = Bookmark.objects.get_or_create(
            user=request.user,
            project=project,
            defaults={'property': None}
        )
        
        if not created:
            bookmark.delete()
            return JsonResponse({'status': 'removed', 'message': 'Bookmark removed successfully'})
        
        return JsonResponse({'status': 'added', 'message': 'Bookmark added successfully'})
    
    except Project.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Project not found'}, status=404)
    except ValidationError as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': 'An error occurred'}, status=500)
    

def property_list(request):
    # Initialize filter parameters with safe defaults
    filter_params = {
        'city': request.GET.get('city', ''),
        'locality': request.GET.get('locality', ''),
        'property_type': request.GET.get('property_type', ''),
        'min_price': request.GET.get('min_price', ''),
        'max_price': request.GET.get('max_price', ''),
        'price_range': request.GET.get('price_range', '50000000'),  # Default 50L
        'bedrooms': request.GET.get('bedrooms', ''),
        'min_area': request.GET.get('min_area', ''),
        'max_area': request.GET.get('max_area', ''),
        'construction_status': request.GET.getlist('construction_status', []),
        'furnishing': request.GET.getlist('furnishing', []),
        'amenities': request.GET.getlist('amenities', []),
        'rera_approved': request.GET.get('rera_approved') == 'on',
        'gated_community': request.GET.get('gated_community') == 'on',
        'pet_friendly': request.GET.get('pet_friendly') == 'on',
        'negotiable': request.GET.get('negotiable') == 'on',
        'per_page': request.GET.get('per_page', '12'),
    }

    # Start with base queryset
    properties = Property.objects.all().order_by('-created_at')

    # Apply filters with proper type conversion and validation
    if filter_params['city']:
        properties = properties.filter(city__iexact=filter_params['city'])

    if filter_params['locality']:
        properties = properties.filter(
            Q(address__icontains=filter_params['locality']) | 
            Q(society_name__icontains=filter_params['locality'])
        )

    if filter_params['property_type']:
        properties = properties.filter(property_type=filter_params['property_type'])

    # Price filters (combine slider and manual inputs)
    price_filters = Q()
    try:
        price_value = Decimal(filter_params['price_range'])
        price_filters |= Q(price_in_rs__gte=price_value * Decimal('0.9'))  # 10% buffer
        price_filters |= Q(price_in_rs__lte=price_value * Decimal('1.1'))
    except (InvalidOperation, TypeError):
        pass

    try:
        if filter_params['min_price']:
            min_price = Decimal(filter_params['min_price'])
            price_filters &= Q(price_in_rs__gte=min_price)
        if filter_params['max_price']:
            max_price = Decimal(filter_params['max_price'])
            price_filters &= Q(price_in_rs__lte=max_price)
    except (InvalidOperation, TypeError):
        pass

    if price_filters:
        properties = properties.filter(price_filters)

    # BHK configuration
    if filter_params['bedrooms']:
        properties = properties.filter(number_of_bedrooms=filter_params['bedrooms'])

    # Area filters
    area_filters = Q()
    try:
        if filter_params['min_area']:
            min_area = Decimal(filter_params['min_area'])
            area_filters &= Q(carpet_area__gte=min_area)
        if filter_params['max_area']:
            max_area = Decimal(filter_params['max_area'])
            area_filters &= Q(carpet_area__lte=max_area)
    except (InvalidOperation, TypeError):
        pass

    if area_filters:
        properties = properties.filter(area_filters)

    # Construction status filter
    if filter_params['construction_status']:
        properties = properties.filter(construction_status__in=filter_params['construction_status'])

    # Furnishing status filter
    if filter_params['furnishing']:
        properties = properties.filter(furnishing_status__in=filter_params['furnishing'])

    # Amenities filter (with distinct to avoid duplicates)
    if filter_params['amenities']:
        try:
            amenity_ids = [int(a) for a in filter_params['amenities'] if a.isdigit()]
            if amenity_ids:
                properties = properties.filter(amenities__id__in=amenity_ids).distinct()
        except (ValueError, TypeError):
            pass

    # Boolean filters
    if filter_params['rera_approved']:
        properties = properties.filter(rera_approved=True)
    
    if filter_params['gated_community']:
        properties = properties.filter(gated_community=True)
    
    if filter_params['pet_friendly']:
        properties = properties.filter(pet_friendly=True)
    
    if filter_params['negotiable']:
        properties = properties.filter(negotiable=True)

    # Get distinct values for filter options (optimized queries)
    filter_options = {
        'cities': Property.objects.values_list('city', flat=True)
                       .distinct().order_by('city'),
        'property_types': Property.PropertyType.choices,
        'bedroom_choices': Property.NumberOfBedrooms.choices,
        'construction_statuses': Property.ConstructionStatus.choices,
        'furnishing_statuses': Property.FurnishingStatus.choices,
        'amenities': Amenity.objects.all().order_by('name'),
    }

    # Pagination with error handling
    try:
        per_page = int(filter_params['per_page'])
        per_page = max(1, min(per_page, 100))  # Enforce reasonable limits
    except (ValueError, TypeError):
        per_page = 12

    paginator = Paginator(properties, per_page)
    page_number = request.GET.get('page', 1)

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # Prepare context
    context = {
        'properties': page_obj,
        'selected_filters': filter_params,
        'selected_construction_statuses': filter_params['construction_status'],
        'selected_furnishing_statuses': filter_params['furnishing'],
        'selected_amenities': [int(a) for a in filter_params['amenities'] if a.isdigit()],
        **filter_options
    }

    return render(request, 'property/property_list.html', context)

class ReviewMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        
        # Calculate rating stats
        reviews = obj.reviews.filter(is_approved=True)
        total_reviews = reviews.count()
        
        if total_reviews > 0:
            avg_rating = round(sum(r.rating for r in reviews) / total_reviews, 1)
            rating_distribution = {
                5: reviews.filter(rating=5).count(),
                4: reviews.filter(rating=4).count(),
                3: reviews.filter(rating=3).count(),
                2: reviews.filter(rating=2).count(),
                1: reviews.filter(rating=1).count()
            }
            
            # For projects, calculate category averages
            if hasattr(obj, 'projectreview'):
                category_ratings = {
                    'design': round(sum(r.design_rating for r in reviews) / total_reviews, 1),
                    'location': round(sum(r.location_rating for r in reviews) / total_reviews, 1),
                    'amenities': round(sum(r.amenities_rating for r in reviews) / total_reviews, 1),
                    'value': round(sum(r.value_rating for r in reviews) / total_reviews, 1),
                }
                context['category_ratings'] = category_ratings
            
            # For properties, calculate category averages
            if hasattr(obj, 'propertyreview'):
                category_ratings = {
                    'condition': round(sum(r.condition_rating for r in reviews) / total_reviews, 1),
                    'neighborhood': round(sum(r.neighborhood_rating for r in reviews) / total_reviews, 1),
                    'value': round(sum(r.value_rating for r in reviews) / total_reviews, 1),
                }
                context['category_ratings'] = category_ratings
        else:
            avg_rating = 0
            rating_distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
            context['category_ratings'] = {}
        
        context.update({
            'avg_rating': avg_rating,
            'total_reviews': total_reviews,
            'rating_distribution': rating_distribution,
            'reviews': reviews.order_by('-is_featured', '-created_at'),
            'review_form': self.review_form_class(),
            'user_has_reviewed': self.request.user.is_authenticated and 
                                reviews.filter(user=self.request.user).exists(),
            'user_can_review': self.request.user.is_authenticated and 
                             not reviews.filter(user=self.request.user).exists()
        })
        return context

class ProjectDetailView(ReviewMixin, DetailView):
    model = Project
    template_name = 'project/project_detail.html'
    review_form_class = ProjectReviewForm

class PropertyDetailView(ReviewMixin, DetailView):
    model = Property
    template_name = 'property_detail.html'
    review_form_class = PropertyReviewForm

@login_required
def submit_project_review(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # Check if user already reviewed this project
    if ProjectReview.objects.filter(user=request.user, project=project).exists():
        messages.warning(request, _('You have already reviewed this project.'))
        return redirect('project_detail', pk=pk)
    
    if request.method == 'POST':
        form = ProjectReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.project = project
            review.is_approved = False  # Needs moderation
            
            # Set category based on highest sub-rating
            ratings = {
                'design': int(form.cleaned_data['design_rating']),
                'location': int(form.cleaned_data['location_rating']),
                'amenities': int(form.cleaned_data['amenities_rating']),
                'value': int(form.cleaned_data['value_rating']),
            }
            review.category = max(ratings, key=ratings.get)
            
            review.save()
            
            # Update project rating stats
            project.update_rating_stats()
            
            messages.success(request, _('Thank you for your review! It will be visible after approval.'))
            return redirect('project_detail', pk=pk)
        else:
            messages.error(request, _('Please correct the errors in your review.'))
    else:
        form = ProjectReviewForm()
    
    return redirect('project_detail', pk=pk)

@login_required
def submit_property_review(request, pk):
    property = get_object_or_404(Property, pk=pk)
    
    # Check if user already reviewed this property
    if PropertyReview.objects.filter(user=request.user, property_link=property).exists():
        messages.warning(request, _('You have already reviewed this property.'))
        return redirect('property_detail', pk=pk)
    
    if request.method == 'POST':
        form = PropertyReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.property_link = property
            review.is_approved = False  # Needs moderation
            
            # Set category based on highest sub-rating
            ratings = {
                'condition': int(form.cleaned_data['condition_rating']),
                'neighborhood': int(form.cleaned_data['neighborhood_rating']),
                'value': int(form.cleaned_data['value_rating']),
            }
            review.category = max(ratings, key=ratings.get)
            
            review.save()
            
            # Update property rating stats
            property.update_rating_stats()
            
            messages.success(request, _('Thank you for your review! It will be visible after approval.'))
            return redirect('property_detail', pk=pk)
        else:
            messages.error(request, _('Please correct the errors in your review.'))
    else:
        form = PropertyReviewForm()
    
    return redirect('property_detail', pk=pk)


def log_search(request, query, search_type, results_count, filters):
    """Log search queries for analytics and suggestions"""
    user = request.user if request.user.is_authenticated else None
    user_agent = parse(request.META.get('HTTP_USER_AGENT', ''))
    
    try:
        # Create or update search suggestion
        if query:
            suggestion, created = SearchSuggestion.objects.get_or_create(
                term=query.lower(),
                search_type=search_type,
                defaults={'weight': 1.0}
            )
            if not created:
                suggestion.increment_use()
        
        # Create the search log entry
        SearchQueryLog.objects.create(
            user=user,
            search_type=search_type,
            query={
                'q': query,
                'filters': filters,
                'path': request.path,
            },
            results_count=results_count,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=str(user_agent),
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to log search: {str(e)}")

@require_GET
def unified_search(request):
    """
    Handle all search requests from different interfaces
    """
    search_type = request.GET.get('type', 'property')  # property|project
    query = request.GET.get('q', '').strip()
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Get all filter parameters
    filters = {
        'property_type': request.GET.get('property_type'),
        'price_range': request.GET.get('price_range'),
        'number_of_bedrooms': request.GET.get('number_of_bedrooms'),
        'amenities': request.GET.getlist('amenities'),
        'city': request.GET.get('city'),
        'locality': request.GET.get('locality'),
        'min_price': request.GET.get('min_price'),
        'max_price': request.GET.get('max_price'),
        
    }
    
    try:
        if search_type == 'project':
            results = search_projects(query, filters)
            template = 'project/project_list.html'
        else:
            results = search_properties(query, filters)
            template = 'property/property_list.html'
        
        # Log the search
        log_search(request, query, search_type.upper(), results.count(), filters)
        
        if is_ajax:
            suggestions = get_search_suggestions(query, search_type.upper())
            return JsonResponse({
                'results': [{
                    'id': r.id,
                    'name': r.name if hasattr(r, 'name') else r.property_code,
                    'type': search_type,
                    'city': r.city,
                } for r in results[:5]],
                'suggestions': [s.term for s in suggestions],
            })
        
        # Prepare context based on search type
        if search_type == 'project':
            context = prepare_project_context(results, request, filters)
        else:
            context = prepare_property_context(results, request, filters)
        
        context.update({
            'query': query,
            'search_type': search_type,
            'filters': filters,
        })
        
        return render(request, template, context)
    
    except Exception as e:
        if is_ajax:
            return JsonResponse({'error': str(e)}, status=500)
        raise

def search_properties(query, filters):
    """Search properties with full-text search and filters"""
    properties = Property.objects.all()
    
    # Full-text search
    if query:
        search_query = SearchQuery(query, config='english')
        properties = properties.annotate(
            rank=SearchRank('search_vector', search_query)
        ).filter(search_vector=search_query).order_by('-rank')
    
    # Apply filters
    if filters.get('property_type'):
        properties = properties.filter(property_type=filters['property_type'])
    
    if filters.get('number_of_bedrooms'):
        properties = properties.filter(number_of_bedrooms=filters['number_of_bedrooms'])
    
    if filters.get('city'):
        properties = properties.filter(city__iexact=filters['city'])
    
    if filters.get('locality'):
        properties = properties.filter(
            Q(address__icontains=filters['locality']) | 
            Q(society_name__icontains=filters['locality'])
        )
    
    # Price range filter
    price_filters = Q()
    try:
        if filters.get('price_range'):
            price_value = Decimal(filters['price_range'])
            if price_value == 5000000:  # Under 50L
                price_filters &= Q(price_in_rs__lte=5000000)
            elif price_value == 10000000:  # 50L-1Cr
                price_filters &= Q(price_in_rs__gte=5000000, price_in_rs__lte=10000000)
            elif price_value == 20000000:  # 1Cr-2Cr
                price_filters &= Q(price_in_rs__gte=10000000, price_in_rs__lte=20000000)
            elif price_value == 20000001:  # Above 2Cr
                price_filters &= Q(price_in_rs__gte=20000000)
    except (InvalidOperation, TypeError):
        pass
    
    # Manual price range
    try:
        if filters.get('min_price'):
            min_price = Decimal(filters['min_price'])
            price_filters &= Q(price_in_rs__gte=min_price)
        if filters.get('max_price'):
            max_price = Decimal(filters['max_price'])
            price_filters &= Q(price_in_rs__lte=max_price)
    except (InvalidOperation, TypeError):
        pass
    
    if price_filters:
        properties = properties.filter(price_filters)
    
    # Amenities filter
    if filters.get('amenities'):
        try:
            amenity_ids = [int(a) for a in filters['amenities'] if a.isdigit()]
            if amenity_ids:
                properties = properties.filter(amenities__id__in=amenity_ids).distinct()
        except (ValueError, TypeError):
            pass
    
    # Boolean filters
    if filters.get('rera_approved') == 'on':
        properties = properties.filter(rera_approved=True)
    
    if filters.get('gated_community') == 'on':
        properties = properties.filter(gated_community=True)
    
    return properties.order_by('-created_at')

def search_projects(query, filters):
    """Search projects with full-text search and filters"""
    projects = Project.objects.all()
    
    # Full-text search
    if query:
        search_query = SearchQuery(query, config='english')
        projects = projects.annotate(
            rank=SearchRank('search_vector', search_query)
        ).filter(search_vector=search_query).order_by('-rank')
    
    # Apply filters
    if filters.get('property_type'):
        projects = projects.filter(property_type=filters['property_type'])
    
    if filters.get('city'):
        projects = projects.filter(city__iexact=filters['city'])
    
    if filters.get('locality'):
        projects = projects.filter(locality__icontains=filters['locality'])
    
    # Price range filter
    price_filters = Q()
    try:
        if filters.get('price_range'):
            price_value = Decimal(filters['price_range'])
            if price_value == 5000000:  # Under 50L
                price_filters &= Q(price_range_end__lte=5000000)
            elif price_value == 10000000:  # 50L-1Cr
                price_filters &= Q(price_range_start__gte=5000000, price_range_end__lte=10000000)
            elif price_value == 20000000:  # 1Cr-2Cr
                price_filters &= Q(price_range_start__gte=10000000, price_range_end__lte=20000000)
            elif price_value == 20000001:  # Above 2Cr
                price_filters &= Q(price_range_start__gte=20000000)
    except (InvalidOperation, TypeError):
        pass
    
    # Manual price range
    try:
        if filters.get('min_price'):
            min_price = Decimal(filters['min_price'])
            price_filters &= Q(price_range_start__gte=min_price)
        if filters.get('max_price'):
            max_price = Decimal(filters['max_price'])
            price_filters &= Q(price_range_end__lte=max_price)
    except (InvalidOperation, TypeError):
        pass
    
    if price_filters:
        projects = projects.filter(price_filters)
    
    # Amenities filter
    if filters.get('amenities'):
        try:
            amenity_ids = [int(a) for a in filters['amenities'] if a.isdigit()]
            if amenity_ids:
                projects = projects.filter(amenities__id__in=amenity_ids).distinct()
        except (ValueError, TypeError):
            pass
    
    return projects.order_by('-created_at')




def get_search_suggestions(query, search_type=None, limit=5):
    """Get search suggestions based on query"""
    if len(query) < 2:
        return []
    
    suggestions = SearchSuggestion.objects.filter(
        Q(term__istartswith=query.lower()) |
        Q(term__icontains=f' {query.lower()}')  # Also match words within terms
    )
    
    if search_type:
        suggestions = suggestions.filter(search_type=search_type)
    
    # Prioritize exact matches and higher weight/use_count
    return suggestions.annotate(
        exact_match=Case(
            When(term__istartswith=query.lower(), then=1),
            default=0,
            output_field=IntegerField()
        )
    ).order_by('-exact_match', '-weight', '-use_count')[:limit]




def prepare_project_context(projects, request, filters):
    """Prepare context for project list view"""
    # Pagination
    per_page = int(request.GET.get('per_page', 12))
    paginator = Paginator(projects, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Filter options
    filter_options = {
        'cities': Project.objects.values_list('city', flat=True)
                       .distinct().order_by('city'),
        'developers': Project.objects.values_list('developed_by', flat=True)
                         .distinct().order_by('developed_by'),
        'amenities': Amenity.objects.all().order_by('name'),
        'project_types': Project.PropertyType.choices,
    }
    
    return {
        'projects': page_obj,
        'selected_filters': filters,
        'selected_amenities': [int(a) for a in filters.get('amenities', []) if a.isdigit()],
        **filter_options
    }

def prepare_property_context(properties, request, filters):
    """Prepare context for property list view"""
    # Pagination
    per_page = int(request.GET.get('per_page', 12))
    paginator = Paginator(properties, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Filter options
    filter_options = {
        'cities': Property.objects.values_list('city', flat=True)
                       .distinct().order_by('city'),
        'property_types': Property.PropertyType.choices,
        'bedroom_choices': Property.NumberOfBedrooms.choices,
        'construction_statuses': Property.ConstructionStatus.choices,
        'furnishing_statuses': Property.FurnishingStatus.choices,
        'amenities': Amenity.objects.all().order_by('name'),
    }
    
    return {
        'properties': page_obj,
        'selected_filters': filters,
        'selected_amenities': [int(a) for a in filters.get('amenities', []) if a.isdigit()],
        **filter_options
    }


@require_GET
def search_suggestions(request):
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'property')
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    try:
        # Get suggestions from database
        suggestions = get_search_suggestions(query, search_type.upper())
        suggestions_list = [
            {'term': s.term, 'count': s.use_count} 
            for s in suggestions[:5]
        ]
    except Exception as e:
        # Fallback if table doesn't exist yet
        suggestions_list = []
    
    # If not enough suggestions, search in projects/properties
    if len(suggestions_list) < 5:
        remaining = 5 - len(suggestions_list)
        if search_type == 'project':
            # Search across all relevant project fields
            projects = Project.objects.filter(
                Q(name__icontains=query) |
                Q(locality__icontains=query) |
                Q(city__icontains=query) |
                Q(district__icontains=query) |
                Q(state__icontains=query) |
                Q(address__icontains=query) |
                Q(landmark__icontains=query) |
                Q(developed_by__icontains=query)
            ).annotate(
                display_text=Case(
                    When(name__icontains=query, then=Concat(
                        'name', Value(' - '), 'locality', Value(', '), 'city',
                        output_field=CharField()
                    )),
                    When(locality__icontains=query, then=Concat(
                        'name', Value(' - '), 'locality', Value(', '), 'city',
                        output_field=CharField()
                    )),
                    default=Concat(
                        'name', Value(' - '), 'city',
                        output_field=CharField()
                    ),
                    output_field=CharField()
                )
            ).values('display_text').distinct()[:remaining]
            
            suggestions_list.extend([
                {'term': item['display_text'], 'count': None} 
                for item in projects
            ])
        else:
            # Search across all relevant property fields
            properties = Property.objects.filter(
                Q(property_code__icontains=query) |
                Q(city__icontains=query) |
                Q(locality__icontains=query) |
                Q(district__icontains=query) |
                Q(state__icontains=query) |
                Q(address__icontains=query) |
                Q(society_name__icontains=query) |
                Q(landmark__icontains=query)
            ).annotate(
                display_text=Case(
                    When(society_name__icontains=query, then=Concat(
                        'society_name', Value(', '), 'address',
                        output_field=CharField()
                    )),
                    When(address__icontains=query, then=Concat(
                        'society_name', Value(', '), 'address',
                        output_field=CharField()
                    )),
                    When(city__icontains=query, then=Concat(
                        'society_name', Value(', '), 'city',
                        output_field=CharField()
                    )),
                    default=Concat(
                        'property_code', Value(' - '), 'city',
                        output_field=CharField()
                    ),
                    output_field=CharField()
                )
            ).values('display_text').distinct()[:remaining]
            
            suggestions_list.extend([
                {'term': prop['display_text'], 'count': None} 
                for prop in properties
            ])
    
    # Deduplicate suggestions while preserving order
    seen = set()
    deduped_suggestions = []
    for s in suggestions_list[:5]:
        term = s['term']
        if term not in seen:
            seen.add(term)
            deduped_suggestions.append(s)
    
    return JsonResponse({
        'suggestions': deduped_suggestions
    })




@login_required
def my_bookmarks(request):
    # Get all bookmarks for the current user
    bookmarks = Bookmark.objects.filter(user=request.user).select_related('property', 'project')
    
    # Pagination
    paginator = Paginator(bookmarks, 12)  # Show 12 bookmarks per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'bookmarks': page_obj,
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1,
    }
    return render(request, 'bookmark.html', context)

@login_required
@require_POST
@csrf_exempt  # For simplicity in this example, in production use proper CSRF handling
def remove_bookmark(request, bookmark_id):
    try:
        bookmark = get_object_or_404(Bookmark, id=bookmark_id, user=request.user)
        bookmark.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)
    

    
@login_required
def add_property_bookmark(request, property_id):
    property = get_object_or_404(Property, id=property_id)
    bookmark, created = Bookmark.objects.get_or_create(
        user=request.user,
        property=property
    )
    if created:
        return JsonResponse({
            'success': True, 
            'action': 'added',
            'bookmark_id': bookmark.id
        })
    return JsonResponse({'success': False, 'message': 'Already bookmarked'})

@login_required
def add_project_bookmark(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    bookmark, created = Bookmark.objects.get_or_create(
        user=request.user,
        project=project
    )
    if created:
        return JsonResponse({
            'success': True, 
            'action': 'added',
            'bookmark_id': bookmark.id
        })
    return JsonResponse({'success': False, 'message': 'Already bookmarked'})




