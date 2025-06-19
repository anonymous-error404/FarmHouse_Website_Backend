import os

from django.test import TestCase
from . import views

class Randomtests(TestCase):
    print(os.environ.get('GMAIL_app_password'))