from rest_framework import serializers
from .models import *

class IdentitySerializer(serializers.ModelSerializer):
    class Meta: 
        model = Identity
        fields = '__all__' 

    #----validate that the legal identity hasnt been created already for this user: after all everyone only has 1 legal identity-----#
    def validate_identity_type(self, value):
        user = self.initial_data.get('user')
        if value.lower() == "legal":
            if Identity.objects.filter(user=user, identity_type__iexact="legal").exists():
                raise serializers.ValidationError(
                    "A legal identity already exists for this user."
                )
        return value


#---for the contexts----#
class ContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = Context
        fields = ["context_name", "linked_user"]


#-----for the new status updates------#
class NotificationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotifications
        fields = ["user", "notification_content", "created_date"]


#----------------For the API clients---------------#
class APIClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIClient
        fields = [
            "id",
            "client_name",
            "api_key",
            "priority_identity",
            "linked_user"
        ]


# class UserNotifications(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     notification_content = models.TextField(max_length=256, null=False, blank=False)
#     created_date = models.DateTimeField(auto_now_add=True)
#     is_read = models.BooleanField(default=False)

#     def __str__(self):
#         return f"Status update by {self.user.username} on {self.created_date}"


