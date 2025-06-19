import base64
from rest_framework import serializers
from . import utils
from FarmHouse_Website.models import *


class EncodeWhileWriteOnly(serializers.Field):
    def to_representation(self, value):
        if value is not None:
            return base64.b64encode(value).decode('utf-8') #used to create a string of b64 encoded binary data(media file) for safe wrapping into json
        return None

    def to_internal_value(self, value):
        if value is not None:
            return utils.get_encoded_media(value)
        return None


class BookingsSerializer(serializers.ModelSerializer):
    IDimage = EncodeWhileWriteOnly()
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
        write_only_fields = ['IDimage']


class MenuSerializer(serializers.ModelSerializer):
    dishImage = EncodeWhileWriteOnly()

    class Meta:
        model = Menu
        fields = [
            'dishId',
            'dishName',
            'dishDescription',
            'dishPrice',
            'dishImage',
        ]

class ReviewsSerializer(serializers.ModelSerializer):
    reviewDate = serializers.DateField(required=False)

    class Meta:
        model = Reviews
        fields = '__all__'


