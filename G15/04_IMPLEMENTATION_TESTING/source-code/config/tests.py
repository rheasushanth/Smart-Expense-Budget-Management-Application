import importlib.util
import os
from pathlib import Path
from unittest import mock

from django.db import connection
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

SETTINGS_FILE = Path(__file__).resolve().parent / "settings.py"


def load_settings(**environment):
    """Import settings.py fresh under a given environment.

    Loaded under a throwaway module name rather than reloaded in place, so
    the settings object the running test suite is using is left alone.
    """
    spec = importlib.util.spec_from_file_location(
        "config._settings_under_test", SETTINGS_FILE
    )
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(os.environ, environment, clear=False):
        spec.loader.exec_module(module)
    return module


class DebugFailsClosedTest(SimpleTestCase):
    """SEC-004, issue #61: the production security block must not be skippable.

    DJANGO_DEBUG previously defaulted to True, so a deployment that did not
    set it ran with the whole `if not DEBUG:` block skipped — no SSL
    redirect, no secure cookies, no nosniff, no frame-deny — while still
    serving traffic with nothing signalling the problem.
    """

    # The five controls that the production block switches on. Named here so
    # that dropping one in a later refactor fails this test rather than
    # silently weakening a deployment.
    PRODUCTION_CONTROLS = {
        "SECURE_SSL_REDIRECT": True,
        "SESSION_COOKIE_SECURE": True,
        "CSRF_COOKIE_SECURE": True,
        "SECURE_CONTENT_TYPE_NOSNIFF": True,
        "X_FRAME_OPTIONS": "DENY",
    }

    def test_debug_is_false_when_the_variable_is_unset(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            settings_module = load_settings()
        self.assertFalse(settings_module.DEBUG)

    def test_debug_can_be_opted_into_for_local_development(self):
        settings_module = load_settings(DJANGO_DEBUG="True")
        self.assertTrue(settings_module.DEBUG)

    def test_an_unset_variable_still_applies_every_production_control(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            settings_module = load_settings()

        for name, expected in self.PRODUCTION_CONTROLS.items():
            with self.subTest(setting=name):
                self.assertEqual(getattr(settings_module, name), expected)

    def test_production_trusts_the_proxy_forwarded_protocol_header(self):
        """Render terminates TLS at its proxy; without this the redirect loops."""
        with mock.patch.dict(os.environ, {}, clear=True):
            settings_module = load_settings()

        self.assertEqual(
            settings_module.SECURE_PROXY_SSL_HEADER,
            ("HTTP_X_FORWARDED_PROTO", "https"),
        )

    def test_development_does_not_force_https(self):
        """DEBUG=True must not switch on SSL redirect, or runserver breaks."""
        settings_module = load_settings(DJANGO_DEBUG="True")
        self.assertFalse(getattr(settings_module, "SECURE_SSL_REDIRECT", False))


class AvailabilityTest(TestCase):
    """TC-AVAIL-01: Verify application availability."""

    def test_health_endpoint_returns_success(self):
        response = self.client.get(reverse("health_check"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "database": "ok"},
        )

    def test_database_connection_is_usable(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

        self.assertEqual(result[0], 1)
