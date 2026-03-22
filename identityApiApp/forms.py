from django import forms
from django.forms import ModelForm
from .models import *
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, SetPasswordForm, UserChangeForm
from django.contrib.auth import authenticate
#---for password validation---# 
import re

#-----For generating unique usernames (for django's default User's username)-----#
def generate_unique_username():
    base = "user"
    counter = 1
    while True:
        username = f"{base}{counter}"
        if not User.objects.filter(username=username).exists():
            return username
        counter += 1



#-----form for adding in new user-----#
class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    display_name = forms.CharField(
        required=True,
        max_length=150,
        label="Username",
        widget=forms.TextInput(attrs={'placeholder': 'Enter your username'})
    )

    
    class Meta:
        model = User
        fields = ["display_name", "email", "password1", "password2"]

    #-----validating the form------#s
    def clean(self):
        cleaned_data = super().clean()

        # input_username = cleaned_data.get("username")
        input_email = cleaned_data.get("email")
        
        input_display_name = cleaned_data.get("display_name")

        input_password = cleaned_data.get("password1")
# 
        if input_email:
            if User.objects.filter(email=input_email).exists():
                self.add_error("email", "An account with this email already exists.")

        if not input_display_name:
            self.add_error("display_name", "Your username cannot be empty")
        
        if input_display_name:
            if UserProfile.objects.filter(display_name= input_display_name).exists():
                self.add_error("display_name", "This username is already taken.")

        #---Validating password requirements---#
        if input_password:
            if len(input_password) < 8:
                self.add_error("password1", "Password must be at least 8 characters long.")

            if not re.search(r'[A-Z]', input_password):
                self.add_error("password1", "Password must contain at least one uppercase letter.")

            if not re.search(r'[a-z]', input_password):
                self.add_error("password1", "Password must contain at least one lowercase letter.")

            if not re.search(r'\d', input_password):
                self.add_error("password1", "Password must contain at least one digit.")

        #---Note that other validation methods such as "common password" or 
        # "password 1 and 2 dont match will be handled by django's default form errors"-----#

        return self.cleaned_data
    
    def save(self, commit=True):
        # Get user object without saving
        user = super().save(commit=False)
        
        # Assign random internal username
        user.username = generate_unique_username()
        
        # Assign email
        user.email = self.cleaned_data["email"]
        
        # Save user so it has a PK
        user.save()  # Must save here before creating related objects
        
        # Create UserProfile (now user has a PK)
        display_name = self.cleaned_data.get("display_name")
        UserProfile.objects.create(user=user, display_name=display_name)
        
        return user
#---Note that the password will be automatically hashed due to django----#


#----------------form for logging in-------------#
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label = "Enter your Sign-In ID (Email Address)", #---changing the form's title to "Email"-----#
        widget=forms.TextInput(
            attrs={
                'class': 'form-control ',
                'placeholder': 'Enter your Email'
            }
        )
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control ',
            'placeholder': 'Enter your Password'
        })
    )

    #---This is necessary the login form asks for email and password 
    # but django takes the first input as "username"
    def clean(self):        
        #---getting the user's forms inputs-----#
        input_email =    self.cleaned_data.get('username')
        input_password = self.cleaned_data.get("password")

        if input_email and input_password:
            try:
                #---checks that this is a registered email---#
                registered_user = User.objects.get(email=input_email)
                #---gets account's username
                registered_username = registered_user.username
            
            #---when the email doesnt exists-----#
            except User.DoesNotExist:
                #-----For security reasons, never specify that it is just an email issue----#
                self.add_error("username", "Invalid email or password. Please note that both fields are case sensitive")
                return self.cleaned_data

            #----Logging in---------#
            self.user_cache = authenticate(
                self.request,
                username = registered_username,
                password = input_password
            )

            #---if login fail----#
            if self.user_cache is None:
                self.add_error("password", "Invalid email or password. Please note that both fields are case sensitive")
                return self.cleaned_data
            
        return self.cleaned_data
        

#---form for changing password---#
class CustomResetPasswordForm(SetPasswordForm):
    def clean_new_password1(self):
        input_password = self.cleaned_data.get("new_password1")

        if len(input_password) < 8:
            raise forms.ValidationError(
                "Password must be at least 8 characters long."
            )

        if not re.search(r'[A-Z]', input_password):
            raise forms.ValidationError(
                "Password must contain at least one uppercase letter."
            )

        if not re.search(r'[a-z]', input_password):
            raise forms.ValidationError(
                "Password must contain at least one lowercase letter."
            )

        if not re.search(r'\d', input_password):
            raise forms.ValidationError(
                "Password must contain at least one digit."
            )

        return input_password


#---form for updating user profile------#
class CustomProfileUpdateForm(UserChangeForm):
    password = None

    display_name = forms.CharField(
        required=True,
        max_length=150,
        label="Your Account Name",
        widget=forms.TextInput(attrs={'placeholder': 'Your display name'})
    )

    class Meta:
        model = User
        fields = [ "display_name", "email"]  #--Not include User's username----#

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            try:
                self.fields['display_name'].initial = self.instance.userprofile.display_name
            except UserProfile.DoesNotExist:
                self.fields['display_name'].initial = ""

    def save(self, commit=True):
        user = super().save(commit=False)  #(don't touch username)
        display_name = self.cleaned_data.get("display_name")

        #----update UserProfile----#
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.display_name = display_name
        profile.save()

        if commit:
            user.save()  #----saves only the email--------#

        return user



#-----form for adding in a new context--------#
class ContextForm(forms.ModelForm):
    class Meta:
        model = Context
        fields = ["context_name"]

        labels = {"context_name": "New Context:"}

        widgets = {
            "context_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter the new context"
                }
            )
        }


# #---form for adding in a new platform---#
class APIClientForm(forms.ModelForm):
    class Meta:
        model = APIClient
        fields = ["client_name", "priority_identity"]
        labels = {
            "client_name": "Name of the website",
            "priority_identity": "Which identity should this client retrieve?"
        }

        #---making the forms use bootstrap---#
        widgets = {
            "client_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter website name"
            }),

            "priority_identity": forms.Select(attrs={
                "class": "form-select"
            })
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        
        super().__init__(*args, **kwargs)
        self.user = user

        #---so that the user doesnt leave the identity selection blank----#
        self.fields["priority_identity"].required = True
        self.fields["priority_identity"].error_messages["required"] = \
            "Please select an identity for this client."

        if user:
            #----getting just the identities linked to the logged in user that have these 2 visibility levels---#
            self.fields["priority_identity"].queryset = Identity.objects.filter(
                linked_user=user,
                visibility__in=["public", "specific_client"]
            )

    
    def clean_client_name(self):
        client_name = self.cleaned_data.get("client_name")

        if APIClient.objects.filter(
            linked_user=self.user,
             #---making sure it is case senstive, so someone cant just paste the same name but in upper/lower casing--#
            client_name__iexact=client_name
        ).exists():
            raise forms.ValidationError(
                "You already added a client with this name."
            )

        return client_name


class EditAPIClientForm(forms.ModelForm):
    class Meta:
        model = APIClient
        fields = ["client_name", "priority_identity"]
        labels = {
            "client_name": "Name of the website",
            "priority_identity": "Which identity should this client retrieve?"
        }

        widgets = {
            "client_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter website name"
            }),

            "priority_identity": forms.Select(attrs={
                "class": "form-select"
            })
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)
        self.user = user

        self.fields["priority_identity"].required = True
        self.fields["priority_identity"].error_messages["required"] = \
            "Please select an identity for this client."

        if user:
            self.fields["priority_identity"].queryset = Identity.objects.filter(
                linked_user=user,
                visibility__in=["public", "specific_client"]
            )

    def clean_client_name(self):
        client_name = self.cleaned_data.get("client_name")

        duplicate_query = APIClient.objects.filter(
            linked_user=self.user,
            client_name__iexact=client_name
        )

        #------Excluding current instance-----------#
        if self.instance.pk:
            duplicate_query = duplicate_query.exclude(pk=self.instance.pk)

        if duplicate_query.exists():
            raise forms.ValidationError(
                "You already added a client with this name."
            )

        return client_name


#------form for adding in a new identity-----#
class IdentityForm(forms.ModelForm):
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # <-- save the user
        super().__init__(*args, **kwargs)

        # ----Only show contexts belonging to this user
        if self.user:
            self.fields["identity_context"].queryset = Context.objects.filter(
                linked_user=self.user
            )

        #---default empty placeholder
        self.fields["identity_context"].empty_label = "-------"

        #-----Add in the other querysets---------#
        original_qs = self.fields["identity_context"].queryset
        self.fields["identity_context"].choices = [("", "-------"), ("add_new_context", "Add new context")] + [
            (ctx.id, ctx.context_name) for ctx in original_qs
        ]


    class Meta:
        model = Identity
        fields = [
            "identity_name",
            "security_level",
            "visibility",
            "identity_context",
            "related_info"
        ]
        
        labels = {
            "identity_name": "Identity Name",
            "security_level": "Set the Security Level of this identity",
            "visibility": "Who can see this identity?",
            "identity_context": "What is this identity for?", 
            "related_info": "What information would you like to add to this identity?"
        }

        widgets = {
            "identity_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter this identity's name"
                }
            ),

            "security_level": forms.Select(
                attrs={"class": "form-control"}
            ),

            "visibility": forms.Select(
                attrs={"class": "form-control"}
            ),

            "identity_context": forms.Select(
                attrs={"class": "form-control"}
            ),
            
            "related_info": forms.Textarea(attrs={  
                "class": "form-control",
                "rows": 4,
                "placeholder": "Optional extra information regarding this identity"
            }),
        }


    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("identity_name")
        security = cleaned_data.get("security_level")
        visibility = cleaned_data.get("visibility")
        context = cleaned_data.get("identity_context")

        #---Only run this check if all fields are filled-----#
        if name and security and visibility and context:
            duplicate_identity = Identity.objects.filter(
                linked_user=self.user, 
                identity_name=name,
                security_level=security,
                visibility=visibility,
                identity_context=context
            )
           
            # Exclude current instance if editing
            if self.instance.pk:
                duplicate_identity = duplicate_identity.exclude(pk=self.instance.pk)

            if duplicate_identity.exists():
                raise forms.ValidationError("You already made this identity with the same context, security, and visibility.")

        return cleaned_data


class EditIdentityForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # Save the user
        super().__init__(*args, **kwargs)

        # Populate identity_context choices same as IdentityForm
        original_choices = list(self.fields["identity_context"].choices)
        original_choices = [choice for choice in original_choices if choice[0]]

        self.fields["identity_context"].choices = [
            ("", "-------"),
            ("add_new_context", "Add new context")
        ] + original_choices

    class Meta:
        model = Identity
        fields = [
            "identity_name",
            "security_level",
            "visibility",
            "identity_context",
            "related_info"
        ]
        labels = {
            "identity_name": "Identity Name",
            "security_level": "Set the Security Level of this identity",
            "visibility": "Who can see this identity?",
            "identity_context": "What is this identity for?",
            "related_info": "What information would you like to add to this identity?"
        }
        
        widgets = {
            "identity_name": forms.TextInput(attrs={"class": "form-control"}),
            "security_level": forms.Select(attrs={"class": "form-control"}),
            "visibility": forms.Select(attrs={"class": "form-control"}),
            "identity_context": forms.Select(attrs={"class": "form-control"}),
            "related_info": forms.Textarea(attrs={  
                "class": "form-control",
                "rows": 4,
                "placeholder": "Optional extra information regarding this identity"
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("identity_name")
        security = cleaned_data.get("security_level")
        visibility = cleaned_data.get("visibility")
        context = cleaned_data.get("identity_context")

        if name and security and visibility and context:
            duplicate_identity = Identity.objects.filter(
                linked_user=self.user,
                identity_name=name,
                security_level=security,
                visibility=visibility,
                identity_context=context
            )

            # Exclude current instance if editing
            if self.instance.pk:
                duplicate_identity = duplicate_identity.exclude(pk=self.instance.pk)

            if duplicate_identity.exists():
                raise forms.ValidationError(
                    "You already made this identity with the same context, security, and visibility."
                )

        return cleaned_data