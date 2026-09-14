from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    RegisterView,
    MeView,
    ProfileView,
    CustomerCategoryViewSet,
    CustomerViewSet,
    ProductViewSet,
    InvoiceViewSet,
    InvoiceReportView,
)


router = DefaultRouter()

router.register(
    "categories",
    CustomerCategoryViewSet,
    basename="customer-category"
)

router.register(
    "customers",
    CustomerViewSet,
    basename="customer"
)

router.register(
    "products",
    ProductViewSet,
    basename="product"
)

router.register(
    "invoices",
    InvoiceViewSet,
    basename="invoice"
)


urlpatterns = [

    path(
        "register/",
        RegisterView.as_view(),
        name="register"
    ),

    path(
        "me/",
        MeView.as_view(),
        name="me"
    ),

    path(
        "profile/",
        ProfileView.as_view(),
        name="profile"
    ),

    path(
        "invoice-report/",
        InvoiceReportView.as_view(),
        name="invoice-report"
    ),

    path(
        "",
        include(router.urls)
    ),
]