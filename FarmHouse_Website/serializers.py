from rest_framework import serializers
from .models import Bookings
class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookings
        fields = ['bookingId', 'checkInDate', 'checkOutDate', 'paymentStatus', 'guestName', 'guestEmail', 'guestPhone']
        read_only_fields = ['bookingId']

class BookingFullSerializer(serializers.ModelSerializer):
    """Full serializer for admin operations"""
    class Meta:
        model = Bookings
        fields = '__all__'
        read_only_fields = ['bookingId']