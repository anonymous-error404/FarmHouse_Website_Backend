from datetime import datetime, timedelta
from django.db.models import Q
from .models import Bookings

# Define payment status constants for clarity
PAYMENT_STATUS_PENDING = 0
PAYMENT_STATUS_PAID = 1
PAYMENT_STATUS_APPROVED_UNPAID = 2

# List of payment statuses that should block dates (confirmed bookings)
CONFIRMED_PAYMENT_STATUSES = [PAYMENT_STATUS_PAID, PAYMENT_STATUS_APPROVED_UNPAID]

def get_available_dates(start_date, end_date=None, days=30):
    """
    Get a list of available date ranges between start_date and end_date
    or next [days] days if end_date is not provided.
    """
    if not end_date:
        end_date = start_date + timedelta(days=days)
    
    # Get all confirmed bookings in the date range
    bookings = Bookings.objects.filter(
        Q(paymentStatus__in=CONFIRMED_PAYMENT_STATUSES) &
        (
            (Q(checkInDate__gte=start_date) & Q(checkInDate__lte=end_date)) |
            (Q(checkOutDate__gte=start_date) & Q(checkOutDate__lte=end_date)) |
            (Q(checkInDate__lte=start_date) & Q(checkOutDate__gte=end_date))
        )
    ).order_by('checkInDate')
    
    # If no bookings, the whole period is available
    if not bookings:
        return [{'start': start_date, 'end': end_date}]
    
    available_periods = []
    current_date = start_date
    
    # Add periods between bookings
    for booking in bookings:
        if current_date < booking.checkInDate:
            available_periods.append({
                'start': current_date,
                'end': booking.checkInDate - timedelta(days=1)
            })
        current_date = booking.checkOutDate + timedelta(days=1)
    
    # Add period after the last booking
    if current_date <= end_date:
        available_periods.append({
            'start': current_date,
            'end': end_date
        })
    
    return available_periods

# Booking ki availability check karne ke liye utility functions rakha hai.
# get_available_dates function check karta hai ke kisi time range mein kaunse dates available hain booking ke liye.

# Sabse pehle wo database se sirf wo bookings nikalta hai jinka payment status confirm hai
# Uske baad ye dekhta hai ke existing bookings kis date range ko block kar rahi hain, aur phir unke beech ke available dates return karta hai.