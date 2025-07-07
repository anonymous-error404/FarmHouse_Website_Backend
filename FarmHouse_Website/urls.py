from .views import *
from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'bookings', BookingViewSet)
router.register(r'menu', MenuViewSet)
router.register(r'reviews', ReviewsViewSet)

baseUrl = 'NirmalFarms/api'

urlpatterns = [
    path(f'{baseUrl}/', include(router.urls)),
    # path(f'{baseUrl}/otpverification/', Authorization.as_view(), name="otp_verification")
]
