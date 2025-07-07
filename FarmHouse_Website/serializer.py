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

    class Meta:
        model = Bookings
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super(BookingsSerializer, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False


class MenuSerializer(serializers.ModelSerializer):
    dishImage = EncodeWhileWriteOnly(required=False)

    class Meta:
        model = Menu
        fields = [
            'dishId',
            'dishName',
            'dishDescription',
            'dishPrice',
            'dishImage',
            'dishSource',
            'dishCategory',
        ]
        
    def __init__(self, *args, **kwargs):
        super(MenuSerializer, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

class ReviewsSerializer(serializers.ModelSerializer):
    bookingId = serializers.IntegerField(required=False)

    class Meta:
        model = Reviews
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super(ReviewsSerializer, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False


