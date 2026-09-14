from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    Profile,
    CustomerCategory,
    Customer,
    Product,
    Invoice,
)


User = get_user_model()


# =========================================================
# User Serializer
# =========================================================

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User

        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
        ]

        read_only_fields = ["id"]


# =========================================================
# Registration Serializer
# =========================================================

class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        min_length=6
    )

    password2 = serializers.CharField(
        write_only=True
    )

    class Meta:
        model = User

        fields = [
            "username",
            "email",
            "password",
            "password2",
            "first_name",
            "last_name",
        ]

    def validate_email(self, value):

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )

        return value

    def validate_password(self, value):

        if len(value) < 6:
            raise serializers.ValidationError(
                "Password must contain at least 6 characters."
            )

        return value

    def validate(self, attrs):

        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {
                    "password": "Passwords do not match."
                }
            )

        return attrs

    def create(self, validated_data):

        validated_data.pop("password2")

        password = validated_data.pop("password")

        user = User.objects.create_user(
            password=password,
            **validated_data
        )

        Profile.objects.create(user=user)

        return user


# =========================================================
# Profile Serializer
# =========================================================

class ProfileSerializer(serializers.ModelSerializer):

    user = UserSerializer(
        read_only=True
    )

    class Meta:
        model = Profile

        fields = [
            "id",
            "user",
            "phone",
            "address",
            "image",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "user",
            "created_at",
            "updated_at",
        ]

    def validate_phone(self, value):

        if value and not value.replace("+", "").replace(" ", "").isdigit():
            raise serializers.ValidationError(
                "Phone number contains invalid characters."
            )

        return value


# =========================================================
# Customer Category Serializer
# =========================================================

class CustomerCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerCategory

        fields = [
            "id",
            "name",
            "description",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def validate_name(self, value):

        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Category name must contain at least 2 characters."
            )

        return value.strip()


# =========================================================
# Customer Serializer
# =========================================================

class CustomerSerializer(serializers.ModelSerializer):

    category_name = serializers.CharField(
        source="category.name",
        read_only=True
    )

    class Meta:
        model = Customer

        fields = [
            "id",
            "name",
            "email",
            "phone",
            "address",
            "category",
            "category_name",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "category_name",
            "created_at",
            "updated_at",
        ]

    def validate_name(self, value):

        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Customer name must contain at least 2 characters."
            )

        return value.strip()

    def validate_phone(self, value):

        cleaned = value.replace("+", "").replace(" ", "").replace("-","")

        if not cleaned.isdigit():
            raise serializers.ValidationError(
                "Enter a valid phone number."
            )

        return value


# =========================================================
# Product Serializer
# =========================================================

class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product

        fields = [
            "id",
            "name",
            "description",
            "price",
            "stock",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def validate_name(self, value):

        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Product name must contain at least 2 characters."
            )

        return value.strip()

    def validate_price(self, value):

        if value <= Decimal("0"):
            raise serializers.ValidationError(
                "Product price must be greater than 0."
            )

        return value

    def validate_stock(self, value):

        if value < 0:
            raise serializers.ValidationError(
                "Stock cannot be negative."
            )

        return value


# =========================================================
# Invoice Serializer
# =========================================================

class InvoiceSerializer(serializers.ModelSerializer):

    customer_name = serializers.CharField(
        source="customer.name",
        read_only=True
    )

    product_name = serializers.CharField(
        source="product.name",
        read_only=True
    )

    created_by_name = serializers.CharField(
        source="created_by.username",
        read_only=True
    )

    class Meta:
        model = Invoice

        fields = [
            "id",
            "customer",
            "customer_name",
            "product",
            "product_name",
            "quantity",
            "price",
            "total_amount",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "total_amount",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        ]

    def validate_quantity(self, value):

        if value <= 0:
            raise serializers.ValidationError(
                "Quantity must be greater than 0."
            )

        return value

    def validate_price(self, value):

        if value <= Decimal("0"):
            raise serializers.ValidationError(
                "Price must be greater than 0."
            )

        return value

    def validate(self, attrs):

        product = attrs.get("product")

        quantity = attrs.get("quantity")

        if product and quantity:

            # During update, exclude the existing invoice quantity
            invoice = self.instance

            available_stock = product.stock

            if invoice and invoice.product_id == product.id:
                available_stock += invoice.quantity

            if quantity > available_stock:
                raise serializers.ValidationError(
                    {
                        "quantity": (
                            f"Not enough stock. "
                            f"Available stock: {available_stock}"
                        )
                    }
                )

        return attrs