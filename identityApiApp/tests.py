from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

#---Importing the forms, serializers and models---#
from .models import *
from .forms import *
from .serializers import *
from django.contrib.auth.models import User
from .views import *


# Create your tests here.
#-----testing otp----#
class OTPTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="Testpass123!"
        )

    def test_generate_otp_length(self):
        otp = generate_otp()
        self.assertEqual(len(otp), 6)

    def test_otp_created(self):
        UserOTP.objects.create(user=self.user, otp_code="123456")
        self.assertTrue(UserOTP.objects.filter(user=self.user).exists())

    def test_remove_invalid_otp(self):
        UserOTP.objects.create(user=self.user, otp_code="123456")
        removedInvalidOTP(self.user)
        self.assertFalse(UserOTP.objects.filter(user=self.user).exists())



class AuthTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_signup_creates_inactive_user(self):
        response = self.client.post("/signup/", {
            "username": "newUser",
            "email": "new@test.com",
            "password1": "Testpass123!",
            "password2": "Testpass123!"
        })

        user = User.objects.get(username="newUser")
        self.assertFalse(user.is_active)

    def test_login_redirects_to_otp(self):
        User.objects.create_user(
            username="testUser",
            email=  "new@test.com",
            password="Testpass123!"
        )

        response = self.client.post(
            reverse('login'),
            {
                "username": "testUser",
                "email":  "new@test.com",
                "password": "Testpass123!"
            }
        )

        self.assertEqual(response.status_code, 302)  # redirect

