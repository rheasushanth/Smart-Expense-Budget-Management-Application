from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.shortcuts import render


def home(request):
    return render(request, "base.html")


def health_check(request):
    """Check whether the application and database are responding."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        return JsonResponse(
            {"status": "unavailable", "database": "error"},
            status=503,
        )

    return JsonResponse(
        {"status": "ok", "database": "ok"},
        status=200,
    )
