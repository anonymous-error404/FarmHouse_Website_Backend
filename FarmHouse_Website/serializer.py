import base64

from rest_framework import serializers

from FarmHouse_Website.models import Bookings


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

    def get_IDimage(self,obj):
        return f'<img src="data:image/jpeg;base64,{base64.b64encode(obj.IDimage).decode("utf-8")}>'
