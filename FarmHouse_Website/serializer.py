import base64
import datetime

from rest_framework import serializers

from FarmHouse_Website.models import *


class BookingsSerializer(serializers.ModelSerializer):
    IDimage = serializers.SerializerMethodField()
    bookingDate = serializers.SerializerMethodField()

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

    def get_bookingDate(self, obj):
        return datetime.date.today()


class MenuSerializer(serializers.ModelSerializer):

    class Meta:
        model = Menu
        fields = '__all__'
