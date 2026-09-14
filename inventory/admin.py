from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    User,
    Profile,
    CustomerCategory,
    Customer,
    Product,
    Invoice,
)


# =========================================================
# User Admin
# =========================================================

@admin.register(User)
class CustomUserAdmin(UserAdmin):

    list_display = (
        "id",
        "username",
        "email",
        "is_staff",
        "is_active",
    )

    search_fields = (
        "username",
        "email",
    )


# =========================================================
# Profile Admin
# =========================================================

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "phone",
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "phone",
    )


# =========================================================
# Customer Category Admin
# =========================================================

@admin.register(CustomerCategory)
class CustomerCategoryAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "created_at",
    )

    search_fields = (
        "name",
    )


# =========================================================
# Customer Admin
# =========================================================

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "email",
        "phone",
        "category",
        "created_at",
    )

    list_filter = (
        "category",
    )

    search_fields = (
        "name",
        "email",
        "phone",
    )


# =========================================================
# Product Admin
# =========================================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "price",
        "stock",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
    )


# =========================================================
# Invoice Admin
# =========================================================

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "customer",
        "product",
        "quantity",
        "price",
        "total_amount",
        "created_by",
        "created_at",
    )

    list_filter = (
        "created_at",
    )

    search_fields = (
        "customer__name",
        "product__name",
    )

    readonly_fields = (
        "total_amount",
        "created_by",
    )