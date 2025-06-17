import base64
from datetime import datetime

from rest_framework import serializers

from FarmHouse_Website.models import *


class BookingsSerializer(serializers.ModelSerializer):
    IDimage = serializers.SerializerMethodField()
    bookingDate = serializers.DateField(required=False)

    class Meta:
        model = Bookings
        fields = [
            'bookingId',
            'bookingDate',
            'checkInDate',
            'checkOutDate',
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
        read_only_fields = ['bookingId']

    def get_IDimage(self, obj):
        if obj.IDimage:
            return base64.b64encode(obj.IDimage).decode("utf-8")
        return None

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