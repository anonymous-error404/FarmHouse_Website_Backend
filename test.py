import os
import sys
import django
import unittest
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FarmHouse_Website_Backend.settings') #Django environment
django.setup()
 
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from FarmHouse_Website.models import Bookings
from FarmHouse_Website.utils import get_available_dates, CONFIRMED_PAYMENT_STATUSES

class BookingSystemTest(TestCase):
    def setUp(self):
        """Set up test data - creates a confirmed booking for one week"""
        self.client = APIClient()
        self.today = datetime.now().date()
        self.next_week = self.today + timedelta(days=7)
        self.two_weeks = self.today + timedelta(days=14)
        
        # Confirmed booking test data
        self.booking1 = Bookings.objects.create(
            bookingDate=self.today,
            checkInDate=self.today,
            checkOutDate=self.next_week,
            paymentStatus=1,  # Confirmed and paid
            paymentType="Credit Card",
            paymentAmount=5000,
            guestName="Test Guest 1",
            guestEmail="test1@example.com",
            guestPhone="1234567890",
            guestAddress="123 Test St",
            totalGuestsAdults=2,
            totalGuestsChildren=0,
            IDtype="Passport",
            IDnumber="AB123456",
            purposeOfStay="Vacation"
        )
        print(f"Created test booking: {self.booking1.bookingId}")
    
    def test_booking_model(self):
        """Test that booking model stores data correctly"""
        booking = Bookings.objects.get(bookingId=self.booking1.bookingId)
        self.assertEqual(booking.guestName, "Test Guest 1")
        self.assertEqual(booking.paymentStatus, 1)
        self.assertEqual(booking.checkInDate, self.today)
        self.assertEqual(booking.checkOutDate, self.next_week)
        print("✓ Booking model test passed")
    
    def test_available_dates_utility(self):
        """Test that get_available_dates returns correct ranges"""
        available = get_available_dates(self.today, self.today + timedelta(days=30))
        
        
        self.assertEqual(len(available), 1)
        self.assertEqual(available[0]['start'], self.next_week + timedelta(days=1))
        
        # Confirm booking 2
        booking2 = Bookings.objects.create(
            bookingDate=self.today,
            checkInDate=self.today + timedelta(days=15),
            checkOutDate=self.today + timedelta(days=20),
            paymentStatus=2,  # Approved but unpaid
            paymentType="Cash",
            paymentAmount=3000,
            guestName="Test Guest 2",
            guestEmail="test2@example.com",
            guestPhone="0987654321",
            guestAddress="456 Test Ave",
            totalGuestsAdults=1,
            totalGuestsChildren=1,
            IDtype="Driver License",
            IDnumber="XY789012",
            purposeOfStay="Business"
        )
        
        # should now have two available periods
        available = get_available_dates(self.today, self.today + timedelta(days=30))
        self.assertEqual(len(available), 2)
        print("✓ Available dates utility test passed")
    
    def test_edge_cases(self):
        """Test edge cases like consecutive bookings"""
        # Booking that ends exactly when another begins (should be allowed)
        consecutive_booking = Bookings.objects.create(
            bookingDate=self.today,
            checkInDate=self.next_week,  # Starts on the checkout day of booking1
            checkOutDate=self.next_week + timedelta(days=5),
            paymentStatus=0,
            paymentType="Credit Card",
            paymentAmount=3000,
            guestName="Edge Case Guest",
            guestEmail="edge@example.com",
            guestPhone="7777777777",
            guestAddress="555 Edge St",
            totalGuestsAdults=2,
            totalGuestsChildren=0,
            IDtype="Passport",
            IDnumber="GH678901",
            purposeOfStay="Vacation"
        )
        
        # Manually check if dates are available
        from FarmHouse_Website.views import BookingViewSet
        booking_viewset = BookingViewSet()
        available, next_available = booking_viewset.check_availability(
            consecutive_booking.checkInDate, 
            consecutive_booking.checkOutDate
        )
        
        # Should be available since it starts right after booking1 ends 
        self.assertTrue(available)
        
        # Set it to approved
        consecutive_booking.paymentStatus = 1
        consecutive_booking.save()
        
        # Check available dates after consecutive booking
        available = get_available_dates(self.today, self.today + timedelta(days=30))
        
        # Should be one available period after all bookings
        self.assertEqual(available[0]['start'], consecutive_booking.checkOutDate + timedelta(days=1))
        print("✓ Edge cases test passed")

    def test_booking_conflict(self):
        """Test that booking conflicts are detected"""
        # Create a booking that overlaps with booking1
        conflict_check = BookingViewSet().check_availability(
            self.today + timedelta(days=2),  # Inside booking1's range
            self.next_week + timedelta(days=2)  # Extends past booking1
        )
        
        # Conflict detection 
        self.assertFalse(conflict_check[0])  # available should be False
        self.assertIsNotNone(conflict_check[1])  # next_available should be provided
        
        # The next available date should be after the existing booking
        self.assertEqual(conflict_check[1], self.next_week + timedelta(days=1))
        print("✓ Booking conflict detection test passed")


from FarmHouse_Website.views import BookingViewSet

def run_manual_tests():
    """Run manual tests for the booking system"""
    print("\nRUNNING MANUAL BOOKING SYSTEM TESTS")
    print("===================================")
    
   
    today = datetime.now().date()
    next_week = today + timedelta(days=7)
    
   
    Bookings.objects.filter(guestEmail__contains='test').delete()
    
    
    print("\nTest 1: Creating a test booking...")
    test_booking = Bookings.objects.create(
        bookingDate=today,
        checkInDate=today,
        checkOutDate=next_week,
        paymentStatus=1,  # Confirmed
        paymentType="Test",
        paymentAmount=1000,
        guestName="Manual Test",
        guestEmail="manual@test.com",
        guestPhone="1234567890",
        guestAddress="Test Address",
        totalGuestsAdults=2,
        totalGuestsChildren=0,
        IDtype="Test",
        IDnumber="TEST1234",
        purposeOfStay="Testing"
    )
    print(f"  ✓ Created booking ID: {test_booking.bookingId}")
    
    
    print("\nTest 2: Testing conflict detection...")
    booking_viewset = BookingViewSet()
    
    # Check a date range that overlaps with the booking
    available, next_date = booking_viewset.check_availability(
        today + timedelta(days=2),  # During the booking
        today + timedelta(days=9)   # After the booking
    )
    
    if not available:
        print(f"  ✓ Conflict correctly detected")
        print(f"  ✓ Next available date: {next_date}")
    else:
        print(f"  ✗ Failed to detect conflict!")
    
    
    print("\nTest 3: Testing available dates...")
    available_periods = get_available_dates(today, today + timedelta(days=30))
    print(f"  ✓ Found {len(available_periods)} available period(s)")
    for period in available_periods:
        print(f"  ✓ Available from {period['start']} to {period['end']}")
    
    
    print("\nCleaning up test data...")
    Bookings.objects.filter(guestEmail="manual@test.com").delete()
    print("  ✓ Test data removed")
    
    print("\nMANUAL TESTS COMPLETED")

if __name__ == '__main__':
    
    run_manual_tests()
    
    print("\nRUNNING UNITTEST TESTS")
    print("=====================")
    
    # Create a test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(BookingSystemTest)
    
    # Run the test suite
    test_runner = unittest.TextTestRunner(verbosity=2)
    test_runner.run(test_suite)