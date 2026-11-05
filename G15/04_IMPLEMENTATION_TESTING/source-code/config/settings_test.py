"""Settings for the automated test suite.

`settings.py` defaults `DJANGO_DEBUG` to False so that a deployment which
forgets to set it fails closed (issue #61). That default is right for a
deployment and wrong for the test suite: with DEBUG false the production
block switches on transport security, and every test-client request is
answered with a 301 to https:// before it reaches a view, while session and
CSRF cookies are marked Secure and never sent back over plain http.

Only the three transport controls that assume a TLS connection are relaxed
here. `SECURE_CONTENT_TYPE_NOSNIFF` and `X_FRAME_OPTIONS` stay as the
production block sets them, so the suite still runs against them.

This does not weaken the check on the production settings themselves:
`config/tests.py::DebugFailsClosedTest` loads `settings.py` directly from
disk under a controlled environment and asserts that all five controls hold
when `DJANGO_DEBUG` is unset, independently of which settings module the
suite is running under.
"""

from .settings import *  # noqa: F401,F403

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# With DEBUG false the production block also selects WhiteNoise's manifest
# static storage, which refuses to resolve {% static %} without a manifest
# built by collectstatic. Tests render templates without running it, so the
# plain storage backend is used here.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
