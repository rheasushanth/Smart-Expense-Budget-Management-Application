
from functools import wraps
from django.core.exceptions import PermissionDenied


def role_required(role):
    """
    Restrict a view to authenticated users with the required role.
    Return HTTP 403 for users without the required role.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied

            user_role = request.user.role.strip().lower()
            required_role = role.strip().lower()

            # The database stores "Administrator", but views use "admin".
            if required_role == "admin":
                allowed = user_role in ("admin", "administrator")
            else:
                allowed = user_role == required_role

            if not allowed:
                raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return _wrapped_view
    return decorator
