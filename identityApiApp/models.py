from django.db import models
from django.contrib.auth.models import User
#---for the otp----#
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError

# Create your models here.

#---For the identity model later on----#
# low = no verification, medium = 1 time verification, high = always need verification when requested--#  
SECURITY_LEVELS = [
    ("low", "Low: You will receieve notifications from the site whenever your identity is being requested for"),
    ("medium", "Medium: You will receive site notifications and need to enter an OTP for first time said identity is requested and thats all."),
    ("high", "High: An OTP will be required everytime this identity is retrieved")
]

#----For storing the OTP-------#
class UserOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6, blank=True)
    otp_created = models.DateTimeField(null=True, blank=True)

    def is_valid(self):
        if self.otp_created:
            #---adding a 5 minutes max time limit for the otp's validity-----#
            return timezone.now() <= self.otp_created + timedelta(minutes=5)
        return False


#---for the display name(since django user's username dont allow spaces------#
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    #---This name can have spaces--#
    display_name = models.CharField(max_length=150, blank=True, null=False)  

    def __str__(self):
        return self.display_name or self.user.username


#-----for the different context-----#
class Context(models.Model):
    context_name = models.CharField(max_length= 150)

    linked_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_context_api_clients"
    )

    priority_identity = models.ForeignKey(
        "Identity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="priority_for_contexts"
    )
    
    #---for the medium security----#
    verified_users = models.ManyToManyField(
        User,
        blank=True,
        related_name="verified_context_api_clients"
    )

    #---so that each user will not have duplicated identities----#
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["linked_user", "context_name"],
                name="unique_context_per_user"
            )
        ]

    def clean(self):
        if self.priority_identity and self.priority_identity.identity_context != self:
            raise ValidationError("Priority identity must belong to this context.")
    
    def __str__(self):
        return self.context_name

#----for the different client platforms
class APIClient(models.Model):
    client_name = models.CharField(max_length=50)
    api_key = models.CharField(max_length=128, unique=True)
    priority_identity = models.ForeignKey(
        "Identity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="priority_for_client"
    )

    linked_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_api_clients"
    )

    #---for the medium security----#
    verified_users = models.ManyToManyField(
        User,
        blank=True,
        related_name="verified_api_clients"
    )

    def __str__(self):
        return self.client_name

    #----so that client_name is unique for each linked_user----#    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["linked_user", "client_name"],
                name="unique_client_per_user"
            )
        ]


#---The identity model-----#
class Identity(models.Model):
    linked_user = models.ForeignKey(User, on_delete=models.CASCADE)
    identity_name = models.CharField(max_length=255)
    related_info = models.CharField(max_length=500, default="", blank=True)

    security_level = models.CharField(
        max_length=10,
        choices=SECURITY_LEVELS,
        default="low"
    )
    
    visibility = models.CharField(
        max_length=50,
        choices=[
            ("public","Public"),
            ("contextually_restricted","Only for the selected Context"),
            ("specific_client","Only for Specific Client sites")
        ],
        default="public"
    )
    
    #----If linked Context model is deleted = default to being linked to Context model with id = 1 ---#
    identity_context = models.ForeignKey(
        Context,
        on_delete=models.SET_DEFAULT,
        default=1
    )

    def __str__(self):
        return f"{self.identity_name} ({self.identity_context}) "


#________----------model for the user notification----------------__________#
class UserNotifications(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification_content = models.TextField(max_length=256, null=False, blank=False)
    created_date = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Status update by {self.user.username} on {self.created_date}"


