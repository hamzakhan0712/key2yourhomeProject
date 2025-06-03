# middleware.py
from django.utils import timezone
from django.conf import settings
from .models import UserSession

class UserSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Update session before processing the request
        if request.user.is_authenticated and hasattr(request, 'session'):
            session_key = request.session.session_key
            if session_key:
                try:
                    user_session = UserSession.objects.get(
                        session_key=session_key,
                        user=request.user,
                        is_active=True
                    )
                    user_session.last_activity = timezone.now()
                    user_session.save()
                except UserSession.DoesNotExist:
                    # Create new session record if it doesn't exist
                    UserSession.objects.create(
                        user=request.user,
                        session_key=session_key,
                        ip_address=self.get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        remember_me=request.session.get_expiry_age() == settings.SESSION_COOKIE_AGE
                    )

        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    

