import base64
from datetime import datetime

from rest_framework import serializers

from FarmHouse_Website.models import *


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
        read_only_fields = ['bookingId', 'duration']

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


class MenuSerializer(serializers.ModelSerializer):
    dishImage = serializers.SerializerMethodField()

    class Meta:
        model = Menu
        fields = [
            'dishId',
            'dishName',
            'dishDescription',
            'dishPrice',
            'dishImage',
        ]

    def get_dishImage(self, obj):
        if obj.dishImage:
            return base64.b64encode(obj.dishImage).decode("utf-8")
        return None