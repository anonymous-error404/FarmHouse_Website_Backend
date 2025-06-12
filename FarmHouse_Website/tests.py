from datetime import date

from django.test import TestCase
from .models import *


# Create your tests here.

class modelTests(TestCase):

    def test_insertInto_reviewMedia(self):

        try:

            with open('C:/Users/Manas/OneDrive/画像/WhatsApp Image 2025-05-05 at 14.44.34_e80bf389.jpg', 'rb') as f:
                image_data = f.read()

            booking = Bookings.objects.create(
                bookingDate=date(2025, 6, 12),
                checkInDate=date(2025, 6, 15),
                checkOutDate=date(2025, 6, 20),
                paymentStatus=1,
                paymentType="Credit Card",
                paymentAmount=5000,
                guestName="John Doe",
                guestEmail="john@example.com",
                guestPhone="9876543210",
                guestAddress="123 Main Street, City",
                totalGuestsAdults=2,
                totalGuestsChildren=1,
                IDtype="Aadhaar",
                IDnumber="1234-5678-9012",
                IDimage=image_data,
                purposeOfStay="Vacation"
            )
            print(booking)
        except Exception as e:
            print("Something went wrong ", e)

    def test_insertInto_Review(self):

        try:
            review = Reviews.objects.create(
                bookingId=1,
                reviewDate=date(2025, 6, 21),
                rating=4,
                reviewContent="Great stay, friendly staff!"
            )
            print(review)
        except Exception as e:
            print("Something went wrong ", e)

    def test_insertInto_ReviewMedia(self):

        try:
            with open('C:/Users/Manas/OneDrive/画像/WhatsApp Image 2025-05-05 at 14.44.34_e80bf389.jpg', 'rb') as f:
                image_data = f.read()

            reviewMedia = ReviewsMedia.objects.create(
                reviewId=100,
                mediaType="image",
                media=image_data,
            )
            print(reviewMedia)
        except Exception as e:
            print("Something went wrong ", e)
