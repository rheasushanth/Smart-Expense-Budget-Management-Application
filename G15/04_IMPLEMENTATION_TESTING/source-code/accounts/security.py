
from accounts.models import SecurityEvent


def get_client_ip(request):
    """Get the client's IP address when available."""
    return request.META.get("REMOTE_ADDR")


def log_security_event(
    event_type,
    description,
    request=None,
    user=None,
    email="",
):
    """Persist a security-relevant event."""

    ip_address = get_client_ip(request) if request else None

    SecurityEvent.objects.create(
        event_type=event_type,
        description=description,
        user=user,
        email=email,
        ip_address=ip_address,
    )
