import base64
import random
from datetime import datetime, timedelta

from django.core.mail import EmailMessage
from django.db.models import Q

from FarmHouse_Website_Backend import settings
from . import compressor
from .models import Bookings, ReviewsMedia

def check_booking_availability(check_in_date, check_out_date, exclude_booking_id=None):
    """
    Check if dates are available for booking.
    Returns (is_available: bool, conflicting_bookings: QuerySet)
    """
    # Look for any confirmed bookings that overlap with the requested period
    conflicts_query = Bookings.objects.filter(
        Q(paymentStatus="PAID") &
        (
            # Case 1: A booking that starts during the requested period
                (Q(checkInDate__gte=check_in_date) & Q(checkInDate__lt=check_out_date)) |
                # Case 2: A booking that ends during the requested period
                (Q(checkOutDate__gt=check_in_date) & Q(checkOutDate__lte=check_out_date)) |
                # Case 3: A booking that completely spans the requested period
                (Q(checkInDate__lte=check_in_date) & Q(checkOutDate__gte=check_out_date))
        )
    )

    # Exclude current booking if updating existing booking
    if exclude_booking_id:
        conflicts_query = conflicts_query.exclude(bookingId=exclude_booking_id)

    conflicts = []

    for booking in conflicts_query.order_by('checkInDate'):
        conflicts.append({
            'start': booking.checkInDate,
            'end': booking.checkOutDate
        })

    return len(conflicts) != 0, conflicts

def validate_booking_dates(check_in_date, check_out_date):
    """
    Validate booking dates for basic business rules.
    Returns (is_valid: bool, error_message: str)
    """
    try:
        if isinstance(check_in_date, str):
            check_in_date = datetime.strptime(check_in_date, '%Y-%m-%d').date()
        if isinstance(check_out_date, str):
            check_out_date = datetime.strptime(check_out_date, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return False, 'Invalid date format. Please use YYYY-MM-DD.'

    today = datetime.now().date()

    # Check if check-in date is in the past
    if check_in_date < today:
        return False, 'Check-in date cannot be in the past.'

    # Check if check-out date is after check-in date
    if check_out_date < check_in_date:
        return False, 'Check-out date must be after check-in date.'

    # Check if booking duration is reasonable (e.g., max 30 days)
    duration = (check_out_date - check_in_date).days
    if duration > 30:
        return False, 'Maximum booking duration is 30 days.'

    # Check if booking is too far in the future (e.g., max 1 year ahead)
    max_future_date = today + timedelta(days=365)
    if check_in_date > max_future_date:
        return False, 'Bookings can only be made up to 1 year in advance.'

    return True, 'Booking dates are valid'


def get_encoded_media(media):
    encoded_media = None

    if media.name.endswith('.jpg') or media.name.endswith('.png') or media.name.endswith('.jpeg'):
        if media.size >= settings.MAX_UPLOAD_SIZE():
            encoded_media = compressor.compressImageWithBestQuality(media.read())
        else:
            encoded_media = media.read()
    elif media.name.endswith('.mp4'):
        if media.size >= settings.MAX_UPLOAD_SIZE():
            encoded_media = compressor.compress_video_under_10mb(media.read())
        else:
            encoded_media = media.read()

    return encoded_media


def setMedia(media_list, review):
    try:
        for media in media_list:
            ReviewsMedia.objects.create(reviewId=review, mediaType=media.content_type, media=get_encoded_media(media), mediaName = media.name)

        return True
    except Exception as e:
        print(e)
        return False

def getMedia(review_id):
    media_list = []
    try:
        media_entries = ReviewsMedia.objects.filter(reviewId=review_id)
        for media_entry in media_entries:
            media_list.append(
                {
                    'media_name' : media_entry.mediaName,
                    'media_type': media_entry.mediaType,
                    'media' : base64.b64encode(media_entry.media).decode('utf-8')
                }
            )
    except Exception as e:
        print(e)
        media_list.append('Some error occured.')
    finally:
        return media_list


def sendConfirmationEmail(receiver, name, checkin, checkout, phone):

    try:
        print("Sending to:", receiver)

        email1 = EmailMessage(
            subject="🏨 Booking Confirmation – Nirmal Farms",
            body=f""""Dear {name},

                    We are delighted to inform you that your booking at Nirmal Farms has been successfully confirmed! 🌿

                    Your stay is reserved from {checkin} to {checkout} under the name {name}.

                    We truly look forward to hosting you and ensuring you have a relaxing and memorable experience amidst nature and comfort.

                    If you have any special requests or questions before your arrival, feel free to reach out to us.

                    Welcome to Nirmal Farms — your peaceful getaway awaits!

                    Warm regards,
                    The Nirmal Farms Team
                    📞 9870204394
                    📞 9870204424""",
            from_email=settings.EMAIL_HOST_USER,
            to=[receiver]
        )

        email2 = EmailMessage(
            subject="🏨 New Booking Request - Nirmal Farms",
            body=f""""Name : {name},
                      gmail : {receiver},
                      phone number : {phone},
                      checkin date : {checkin},
                      checkout dat e: {checkout}""",
            from_email=settings.EMAIL_HOST_USER,
            to=[settings.EMAIL_HOST_USER]
        )
        
        if email1.send(fail_silently=False) and email2.send(fail_silently=False):
            print("email sent")
            return True
        
        return False
    except Exception as e:
        print(e)
