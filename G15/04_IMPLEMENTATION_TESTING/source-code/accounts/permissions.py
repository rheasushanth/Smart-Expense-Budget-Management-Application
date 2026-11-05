from functools import wraps
from django.core.exceptions import PermissionDenied
from accounts.models import SecurityEvent
from accounts.security import log_security_event


def role_required(role):
    """
    Restrict a view to authenticated users with the required role.
    Log unauthorized access attempts and return HTTP 403.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                log_security_event(
                    SecurityEvent.EventType.UNAUTHORIZED_ACCESS,
                    f"Anonymous user attempted to access {request.path}.",
                    request=request,
                )
                raise PermissionDenied

            user_role = request.user.role.strip().lower()
            required_role = role.strip().lower()

            if required_role == "admin":
                allowed = user_role in ("admin", "administrator")
            else:
                allowed = user_role == required_role

            if not allowed:
                log_security_event(
                    SecurityEvent.EventType.UNAUTHORIZED_ACCESS,
                    f"User attempted to access {request.path} without permission.",
                    request=request,
                    user=request.user,
                    email=request.user.email,
                )
                raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return _wrapped_view
    return decorator