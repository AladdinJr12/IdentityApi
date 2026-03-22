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


#----testing account authentication----------#
class AuthTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_signup_creates_inactive_user(self):
        response = self.client.post(
            reverse("sign-up"), 
            {
                "display_name": "newUser",  
                "email": "new@test.com",
                "password1": "Testpass123!",
                "password2": "Testpass123!"
        })

        self.assertEqual(response.status_code, 302)

        user = User.objects.get(email="new@test.com") 
        self.assertFalse(user.is_active)

    def test_login_redirects_to_otp(self):
        User.objects.create_user(
            username="testUser",
            email="new@test.com",
            password="Testpass123!"
        )

        response = self.client.post(
            reverse('login'),
            {
                "username": "new@test.com",   # ---Remeber that I use email and not username---#
                "password": "Testpass123!"
            }
        )
        self.assertEqual(response.status_code, 302)

#----testing identities----#
class IdentityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="new@test.com",
            password="Testpass123!"
        )
        self.client.login(username="testuser", password="Testpass123!")

    def test_create_identity(self):
        context = Context.objects.create(
            context_name="Professional",
            linked_user=self.user
        )

        response = self.client.post(
            reverse('add_identity'),
            {
                "identity_name": "Work Persona",
                "identity_context": context.id,
                "security_level": "low",
                "visibility": "public"
            })

        self.assertEqual(Identity.objects.count(), 1)

    def test_prioritize_identity(self):
        context = Context.objects.create(
            context_name="Work",
            linked_user=self.user
        )

        identity = Identity.objects.create(
            identity_name="Work ID",
            identity_context=context,
            security_level = "low",
            visibility = 'public',
            linked_user=self.user
        )

        self.client.get(f"/prioritize-identity/{identity.id}/")

        context.refresh_from_db()
        self.assertEqual(context.priority_identity, identity)


#------------testing  the api testing page (for mainly the context section)-----#
class APITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="apiuser",
            email="api@test.com",
            password="Testpass123!"
        )

        self.context = Context.objects.create(
            context_name="Work",
            linked_user=self.user
        )

        self.identity = Identity.objects.create(
            identity_name="Professor X",
            identity_context=self.context,
            linked_user=self.user,
            security_level="low"
        )

        self.context.priority_identity = self.identity
        self.context.save()

    def test_get_identity_with_context(self):
        response = self.client.get(
            f"/api/get-identity/{self.context.id}/?email={self.user.email}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["identity_name"], "Professor X")

    def test_invalid_email(self):
        response = self.client.get(
            f"/api/context/{self.context.id}/?email=wrong@test.com"
        )

        self.assertEqual(response.status_code, 404)

    def test_high_security_requires_otp(self):
        self.identity.security_level = "high"
        self.identity.save()

        response = self.client.get(
            f"/api/get-identity/{self.context.id}/?email={self.user.email}"
        )

        self.assertTrue(response.data.get("requires_verification", False))

#-----api testing section for mainly the api key section----# 
class APIKeyTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="clientuser",
            password="Testpass123!"
        )
        self.context = Context.objects.create(
            context_name="TestContext",
            linked_user=self.user
        )


        self.identity = Identity.objects.create(
            identity_name="Client Identity",
            linked_user=self.user,
            security_level="low",
            identity_context=self.context
        )

        self.client_obj = APIClient.objects.create(
            client_name="TestApp",
            api_key="testkey123",
            linked_user=self.user,
            priority_identity=self.identity
        )

    def test_get_api_identity(self):
        response = self.client.get(
            "/api/get-client/?api_key=testkey123"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["identity_name"], "Client Identity")

    def test_invalid_api_key(self):
        response = self.client.get(
            "/api/get-client/?api_key=wrongkey"
        )

        self.assertEqual(response.status_code, 403)

#----testing for the notifications-----#
class NotificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="notifuser",
            password="Testpass123!"
        )

    def test_add_notification(self):
        add_notification(self.user, "Test notification")

        self.assertEqual(UserNotifications.objects.count(), 1)

    def test_check_notifications(self):
        UserNotifications.objects.create(
            user=self.user,
            notification_content="Test"
        )

        client = Client()
        client.login(username="notifuser", password="Testpass123!")

        response = client.get("/check-for-new-notifications/")
        self.assertTrue(response.json()["has_new_updates"])


#---for the "what if" cases----#
class EdgeCaseTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="edgeuser",
            email="edge@test.com",
            password="Testpass123!"
        )

    def test_no_identity_fallback(self):
        context = Context.objects.create(
            context_name="Empty",
            linked_user=self.user
        )

        client = Client()
        response = client.get(
            f"/api/get-identity/{context.id}/?email={self.user.email}"
        )

        self.assertEqual(response.status_code, 200)

    def test_duplicate_context(self):
        Context.objects.create(
            context_name="Work",
            linked_user=self.user
        )

        from rest_framework.test import APIClient
        client = APIClient()
        client.force_authenticate(user=self.user)

        response = client.post( 
        reverse("api_create_context"),                        
        {
            "context_name": "Work"
        })

        self.assertFalse(response.data["success"])


