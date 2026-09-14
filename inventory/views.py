from django.db import transaction
from django.db.models import Sum, Count, DecimalField
from django.db.models.functions import Coalesce
from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import (
    Profile,
    CustomerCategory,
    Customer,
    Product,
    Invoice,
)

from .serializers import (
    UserSerializer,
    RegisterSerializer,
    ProfileSerializer,
    CustomerCategorySerializer,
    CustomerSerializer,
    ProductSerializer,
    InvoiceSerializer,
)

from .permissions import IsStaffOrReadOnly


User = get_user_model()


# =========================================================
# Registration API
# =========================================================

class RegisterView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = RegisterSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response(
            {
                "message": "User registered successfully.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED
        )


# =========================================================
# Current User API
# =========================================================

class MeView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        serializer = UserSerializer(request.user)

        return Response(serializer.data)


# =========================================================
# Profile API
# =========================================================

class ProfileView(APIView):

    permission_classes = [IsAuthenticated]

    def get_profile(self, user):

        profile, created = Profile.objects.get_or_create(
            user=user
        )

        return profile

    def get(self, request):

        profile = self.get_profile(request.user)

        serializer = ProfileSerializer(profile)

        return Response(serializer.data)

    def put(self, request):

        profile = self.get_profile(request.user)

        serializer = ProfileSerializer(
            profile,
            data=request.data,
            partial=False
        )

        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(serializer.data)

    def patch(self, request):

        profile = self.get_profile(request.user)

        serializer = ProfileSerializer(
            profile,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(serializer.data)


# =========================================================
# Customer Category ViewSet
# =========================================================

class CustomerCategoryViewSet(viewsets.ModelViewSet):

    queryset = CustomerCategory.objects.all().order_by("-id")

    serializer_class = CustomerCategorySerializer

    permission_classes = [
        IsStaffOrReadOnly
    ]


# =========================================================
# Customer ViewSet
# =========================================================

class CustomerViewSet(viewsets.ModelViewSet):

    queryset = Customer.objects.select_related(
        "category"
    ).all().order_by("-id")

    serializer_class = CustomerSerializer

    permission_classes = [
        IsAuthenticated
    ]

    search_fields = [
        "name",
        "email",
        "phone",
        "address",
    ]

    filterset_fields = [
        "category",
    ]

    ordering_fields = [
        "id",
        "name",
        "email",
    ]


# =========================================================
# Product ViewSet
# =========================================================

class ProductViewSet(viewsets.ModelViewSet):

    queryset = Product.objects.all().order_by("-id")

    serializer_class = ProductSerializer

    permission_classes = [
        IsStaffOrReadOnly
    ]

    search_fields = [
        "name",
        "description",
    ]

    filterset_fields = [
        "is_active",
    ]

    ordering_fields = [
        "id",
        "name",
        "price",
        "stock",
        "created_at",
    ]


# =========================================================
# Invoice ViewSet
# =========================================================

class InvoiceViewSet(viewsets.ModelViewSet):

    queryset = Invoice.objects.select_related(
        "customer",
        "product",
        "created_by"
    ).all().order_by("-id")

    serializer_class = InvoiceSerializer

    permission_classes = [
        IsStaffOrReadOnly
    ]
    search_fields = [
        "customer__name",
        "customer__email",
        "product__name",
    ]

    filterset_fields = [
        "customer",
        "product",
        "created_by",
    ]

    ordering_fields = [
        "id",
        "quantity",
        "price",
        "total_amount",
        "created_at",
    ]

    @transaction.atomic
    def perform_create(self, serializer):

        product = Product.objects.select_for_update().get(
            pk=serializer.validated_data["product"].pk
        )

        quantity = serializer.validated_data["quantity"]

        if quantity > product.stock:

            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                {
                    "quantity": (
                        f"Not enough stock. "
                        f"Available stock: {product.stock}"
                    )
                }
            )

        product.stock -= quantity

        product.save(
            update_fields=[
                "stock",
                "updated_at"
            ]
        )

        serializer.save(
            created_by=self.request.user
        )

    @transaction.atomic
    def perform_update(self, serializer):

        old_invoice = self.get_object()

        old_product_id = old_invoice.product_id
        old_quantity = old_invoice.quantity

        new_product = serializer.validated_data.get(
            "product",
            old_invoice.product
        )

        new_quantity = serializer.validated_data.get(
            "quantity",
            old_quantity
        )

        # Lock old product
        old_product = Product.objects.select_for_update().get(
            pk=old_product_id
        )

        # If same product
        if new_product.pk == old_product.pk:

            available_stock = (
                old_product.stock + old_quantity
            )

            if new_quantity > available_stock:

                from rest_framework.exceptions import ValidationError

                raise ValidationError(
                    {
                        "quantity": (
                            f"Not enough stock. "
                            f"Available stock: {available_stock}"
                        )
                    }
                )

            old_product.stock = (
                available_stock - new_quantity
            )

            old_product.save(
                update_fields=[
                    "stock",
                    "updated_at"
                ]
            )

        else:

            # Restore old product stock
            old_product.stock += old_quantity

            old_product.save(
                update_fields=[
                    "stock",
                    "updated_at"
                ]
            )

            # Lock new product
            new_product_locked = Product.objects.select_for_update().get(
                pk=new_product.pk
            )

            if new_quantity > new_product_locked.stock:

                from rest_framework.exceptions import ValidationError

                raise ValidationError(
                    {
                        "quantity": (
                            f"Not enough stock. "
                            f"Available stock: "
                            f"{new_product_locked.stock}"
                        )
                    }
                )

            new_product_locked.stock -= new_quantity

            new_product_locked.save(
                update_fields=[
                    "stock",
                    "updated_at"
                ]
            )

        serializer.save(
            created_by=old_invoice.created_by
        )

    @transaction.atomic
    def perform_destroy(self, instance):

        product = Product.objects.select_for_update().get(
            pk=instance.product_id
        )

        # Restore stock
        product.stock += instance.quantity

        product.save(
            update_fields=[
                "stock",
                "updated_at"
            ]
        )

        instance.delete()


# =========================================================
# Invoice Report API
# =========================================================

class InvoiceReportView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        total_invoices = Invoice.objects.count()

        total_sales = Invoice.objects.aggregate(
            total=Coalesce(
                Sum("total_amount"),
                0,
                output_field=DecimalField(
                    max_digits=12,
                    decimal_places=2
                )
            )
        )["total"]

        total_products_sold = Invoice.objects.aggregate(
            total=Coalesce(
                Sum("quantity"),
                0
            )
        )["total"]

        return Response(
            {
                "total_invoices": total_invoices,
                "total_sales": total_sales,
                "total_products_sold": total_products_sold,
            }
        )