from django.db import models

class Bookings(models.Model):
    bookingId = models.AutoField(primary_key=True)
    bookingDate = models.DateField()
    checkInDate = models.DateField()
    checkOutDate = models.DateField()
    paymentStatus = models.IntegerField(default=0)
    paymentType = models.CharField(max_length=100)
    paymentAmount = models.IntegerField(default=0)
    guestName = models.TextField()
    guestEmail = models.CharField(max_length=50)
    guestPhone = models.CharField(max_length=15)
    totalGuestsAdults = models.IntegerField(default=0)
    totalGuestsChildren = models.IntegerField(default=0)
    IDtype = models.CharField(max_length=30) #type of id, eg adhaar, pan etx
    IDnumber = models.CharField(max_length=30, verbose_name="number on ID") #number on id, eg adhar number
    purposeOfStay = models.CharField(max_length=50)


