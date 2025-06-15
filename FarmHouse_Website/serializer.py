import base64
import datetime

from rest_framework import serializers

from FarmHouse_Website.models import *


class BookingsSerializer(serializers.ModelSerializer):
    IDimage = serializers.SerializerMethodField()

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

    def get_IDimage(self, obj):
        return base64.b64encode(obj.IDimage).decode("utf-8")


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
        return base64.b64encode(obj.dishImage).decode("utf-8")
