import base64
from datetime import datetime

from rest_framework import serializers

from FarmHouse_Website.models import Bookings


class BookingsSerializer(serializers.ModelSerializer):
    IDimage = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    bookingDate = serializers.DateField(required=False)  

    class Meta:
        model = Bookings
        fields = [
            'bookingId',
            'bookingDate',
            'checkInDate',
            'checkOutDate',
            'duration',
            'paymentStatus',
            'paymentType',
            'paymentAmount',
            'guestName',
            'guestEmail',
            'guestPhone',
            'guestAddress',
            'totalGuestsAdults',
            'totalGuestsChildren',
            'IDtype',
            'IDnumber',
            'IDimage',
            'purposeOfStay',
        ]
        read_only_fields = ['bookingId', 'duration']  # Remove bookingDate from here

    def get_IDimage(self, obj):
        if obj.IDimage:
            return base64.b64encode(obj.IDimage).decode("utf-8")
        return None
    
    def get_duration(self, obj):
        """Calculate the duration of stay in days"""
        return (obj.checkOutDate - obj.checkInDate).days

    def create(self, validated_data):
        """Override create to set bookingDate if not provided"""
        if 'bookingDate' not in validated_data or validated_data['bookingDate'] is None:
            validated_data['bookingDate'] = datetime.now().date()
        
        return super().create(validated_data)
    
# Ye BookingSerializer class Django REST Framework ka serializer hai jo Bookings model ko represent karta hai.
# jab data frontend se aaye ya backend se jaaye (e.g. API se), to usay readable aur consistent format mein convert kiya ja sake.

# - duration: Stay ka duration calculate kiya ja raha hai (checkOutDate - checkInDate).

# create method override kia agar bookingDate provide nahi to system current date set kar deta hai by default.
