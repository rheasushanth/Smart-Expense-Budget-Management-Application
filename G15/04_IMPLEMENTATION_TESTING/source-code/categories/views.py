from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from accounts.permissions import role_required
from .forms import CategoryForm
from .models import Category


@role_required("admin")
def category_list(request):
    categories = Category.objects.all().order_by("type", "name")
    return render(
        request,
        "categories/category_list.html",
        {"categories": categories},
    )


@role_required("admin")
@require_http_methods(["GET", "POST"])
def category_add(request):
    form = CategoryForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        category = form.save(commit=False)
        category.created_by = request.user
        category.save()
        return redirect("categories:list")

    return render(
        request,
        "categories/category_form.html",
        {"form": form},
    )


@role_required("admin")
@require_http_methods(["GET", "POST"])
def category_edit(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    form = CategoryForm(request.POST or None, instance=category)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("categories:list")

    return render(
        request,
        "categories/category_form.html",
        {"form": form, "category": category},
    )


@role_required("admin")
@require_http_methods(["POST"])
def category_disable(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    category.is_active = False
    category.save(update_fields=["is_active"])
    return redirect("categories:list")


@role_required("admin")
@require_http_methods(["POST"])
def category_enable(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    category.is_active = True
    category.save(update_fields=["is_active"])
    return redirect("categories:list")
