#---for general use----#
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from django.db import DatabaseError

#----for api calls----#
from django.urls import reverse
import requests
from rest_framework.permissions import IsAuthenticated

#----for tracking creation time and removing unverified accounts---#
from datetime import timedelta
from django.utils import timezone

#---Importing the forms, serializers and models---#
from .models import *
from .forms import *
from .serializers import *

#-----for the otp----#
import random
from django.core.mail import send_mail
from django.contrib import messages

#----for reset password----#
from django.contrib.auth.models import User

#----for the add custom context button---#
from django.views.decorators.csrf import csrf_exempt
import json

#----for identity management page------#
from collections import defaultdict

#----for the add client page----#
import secrets

#--------___________For the otp functionality____________--------------#
#-----generate the otp----#
def generate_otp():
    return str(random.randint(100000, 999999))

#----whole otp generation process---#
def otp_generation(request, user, purpose):
    #---Create otp---#
    otp = generate_otp()
    UserOTP.objects.update_or_create(
        user=user, 
        defaults={
            "otp_code": otp,
            "otp_created": timezone.now()
        }
    )

    #---send out the otp to the registered email from my gmail----#
    send_mail(
        "Your Verification Code",
        f"Your OTP code is: {otp}",
        "your_email@gmail.com",
        [user.email],
        fail_silently=False,
    )

    #----saving the user and what this otp is for----#
    request.session["verify_user_id"] = user.id
    request.session["verification_purpose"] = purpose

    return

#---the otp has served its purpose or has expired so its removed---#
def removedInvalidOTP(user):
    UserOTP.objects.filter(user=user).delete()
    return

#----for the resend otp button---#
def resend_otp(request):
    user_id = request.session.get("verify_user_id")
    purpose = request.session.get("verification_purpose")

    #----In case this is called without a sign up or login attempt----#
    if not user_id or not purpose:
        return redirect("login")

    user = get_object_or_404(User, id=user_id)

    #----Deleting the old OTP (if exists)----#
    removedInvalidOTP(user)

    #---Generate a new OTP----#
    otp_generation(request, user, purpose)

    messages.success(request, "A new verification code has been sent.")

    return redirect("verification_page")

#----Removing unverified accounts: this also removes the otp associated with said user-----#
def removeUnverifiedUsers():
    deleted_count, _ = User.objects.filter(
        is_active=False,
        date_joined__lt=timezone.now() - timedelta(minutes=5)
    ).delete()

    if deleted_count > 0:
        print("---Unverified accounts have been deleted---")

#---for directing to the starting page----#
def index(request):
    
    # #----In case this is called without a sign up or login attempt----#
    #---if the user is logged in---#
    if request.user.is_authenticated:
       return redirect("homepage")

    removeUnverifiedUsers()
    return render(request, "htmlTemplates/startingPage.html")

#-------For the sign up page: Adding in a new user--------#
def signup(request):
    # the form for adding in new user
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            
            user = form.save(commit=False)
            user.is_active= False
            user.save()

            #---Create otp---#
            otp_generation(request, user, "signup")

            return redirect("verification_page")

    else:
        form = SignupForm()

    return render(request, "htmlTemplates/signupPage.html", {"signupForm": form})



#-------For the login page--------#
def login_view(request):
    #---if the user was redirected here-----#
    if request.GET.get("next"):
        messages.warning(request, "You need to log in to access that page.")
    
    
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()

        #---Create otp---#
        otp_generation(request, user, "login")

        #---redirect to the verification page----//
        return redirect("verification_page")
    else:
        print(form.errors) #--For debugging purposes--#
    
    return render(request, "htmlTemplates/loginPage.html", {"loginForm": form})

#-----for the verification page------#
def verification_page(request):
    user_id = request.session.get("verify_user_id")
    purpose = request.session.get("verification_purpose")
    

    #----In case this is called without a sign up or login attempt----#
    if not user_id or not purpose:
        return redirect("login")
    
    #---using the id to get the registered user and user_otp---#
    user = get_object_or_404(User, id=user_id)
    user_otp = get_object_or_404(UserOTP, user=user)

    if request.method == "POST":
        entered_otp = request.POST.get("otp")

        if entered_otp == user_otp.otp_code and user_otp.is_valid():

            #---removing the otp from database since it has done its job---#
            removedInvalidOTP(user=user)
            if purpose == "login" or purpose == "signup" or purpose == "Account recovery":
                #---removing verification purpose since it did its job for these purposes---#
                request.session.pop("verification_purpose", None)

            #----redirect to the corresponding path---#
            if purpose == "login" or purpose == "signup":   
                #---adding in default contexts for new accounts----#  
                if purpose == "signup":

                    default_contexts = ["School", "Work", "Social"]
                    for default_context_name in default_contexts:
                        serializer = ContextSerializer(
                            data={"context_name": default_context_name, "linked_user": user.id}
                        )
                        if serializer.is_valid():
                            serializer.save()

                #---removing "verify_user_id" since it has done its job---#
                request.session.pop("verify_user_id", None)
                

                user.is_active = True
                user.save()
                login(request, user)

                return redirect("homepage")

            elif purpose == "Account recovery":

                return redirect("reset_password") 
            
            #---this is the only route where the verification purpose was not removed---#
            #---this is for when the user presses change password in the logged in homepage--#
            elif purpose == "Password reset":
                return redirect("reset_password") 
            
            #-----when verifying for email change----------#
            elif purpose == "Changing your account's registered email":
                new_email = request.session.get("pending_email")
                
                if new_email:
                    user.email = new_email
                    user.save()
                    messages.success(request, f"Your email has been updated to {new_email}.")
                    #---Clean up all of the sessions-----#
                    request.session.pop("pending_email", None)
                    request.session.pop("verify_user_id", None)
                    request.session.pop("verification_purpose", None)

                    #----Add the notification bell---#
                    add_notification(request.user, "You have just updated your profile!")
                    return redirect("homepage")
                else:
                    
                    messages.error(request, "Something went wrong. No pending email found.")
            
            #-----for the api_testing page----#
            if purpose == "api_access":

                #----for the medium security--------#
                pending_api_key = request.session.get("pending_api_key")
                if(pending_api_key):
                    client = get_object_or_404(APIClient, api_key=pending_api_key)
                    client.verified_users.add(user)

                pending_contextID_key = request.session.get("pending_contextID_key")
                if(pending_contextID_key):
                    context = get_object_or_404(Context, id = pending_contextID_key)
                    context.verified_users.add(user)

                messages.success(request, "The identity you requested for has been retreieved")
                return redirect("api_testing") 
            

        else:
            messages.error(request, "Invalid or expired OTP.")

    return render(
        request, 
        "htmlTemplates/verificationPage.html", 
        {"verificationPurpose":purpose}
    )

#---____________________________The homepage after logging in_____________________________----#
@login_required (login_url='login')
def homepage(request):

    user = request.user
    username = UserProfile.objects.filter(user = user).first()

    return render(
        request, 
        "htmlTemplates/homepage.html", 
        {"username": username}
    )

#-----Logs out user then redirects them to starting page-----#
def user_logout(request):
    #---removing "verify_user_id" since it has done its job---#
    request.session.pop("verify_user_id", None)

    logout(request)
    print("A user has logout")
    #---redirect back to homepage-----#
    return redirect('index')


#----________For the reset password page and mechanic________----#
def forget_password(request):
    if request.method == "POST":
        entered_email = request.POST.get("registered_email")
        user = User.objects.filter(email=entered_email).first()
        if(user):
            #---Create otp---#
            otp_generation(request, user, "Account recovery")

            #---redirect to the verification page----//
            return redirect("verification_page")
        else:
            messages.error(request, "No account was found link to that email!")

    return render(
        request, 
        "htmlTemplates/forgetPassword.html"
    )

def reset_password(request):
    user_id = request.session.get("verify_user_id")
    purpose = request.session.get("verification_purpose")
    if not user_id:
        messages.error(request, "No user id found!")
        return redirect("login")

    user = get_object_or_404(User, id=user_id)
    newPasswordForm = CustomResetPasswordForm(user, request.POST or None)

    if request.method == "POST" and newPasswordForm.is_valid():
        #---This will be automatically hashed thanks to django---#
        newPasswordForm.save() 

        #---keep the user logged in if they were logged in when resetting their password----#
        update_session_auth_hash(request, user)

        #---Add success message---#
        messages.success(request, "Password successfully changed!")
        
        if(purpose=="Password reset"):
            #---removing verification purpose since it did its job --#
            request.session.pop("verificationPurpose", None)

            #---removing "verify_user_id" since it has done its job---#
            request.session.pop("verify_user_id", None)

            #---back to homepage now that password changed-----#
            return redirect("homepage")
        
        return redirect("login")
    
    return render(
        request, 
        "htmlTemplates/resetPassword.html",
        {"passwordForm": newPasswordForm}
    )

#----for the reset password button in the home page----#
@login_required (login_url='login') 
def auth_reset_password(request):
    user = request.user

    #---Create otp---#
    otp_generation(request, user, "Password reset")

    #---redirect to the verification page----//
    return redirect("verification_page")

#----------____________________________For the profile page_______________----------#
@login_required (login_url='login') 
def profile_page(request):
    user = request.user
    username = UserProfile.objects.filter(user = user).first()

    return render(
        request, 
        "htmlTemplates/ProfilePage.html",
        {
            "loggedInUser": user,
            "username": username,
        }
    )

@login_required (login_url='login') 
def update_profile(request):    
    form = CustomProfileUpdateForm(request.POST or None, instance = request.user)
    user = request.user

    old_email = user.email

    if request.method == "POST" and form.is_valid():
        new_email = form.cleaned_data.get("email")
        #----checks if the email has been changed---#
        if new_email != old_email:
            #---temporary storing new email---#
            request.session['pending_email'] = new_email
            
            #----Generate OTP that is sent to new email----#
            otp_generation(request, user, purpose="Changing your account's registered email")
            return redirect("verification_page")

        form.save()
        add_notification(request.user, "You have just updated your profile!")
        messages.success( request , "Your profile has been successfully updated ")
        return redirect("homepage")

    return render(
        request, 
        "htmlTemplates/UpdateProfilePage.html",
        {"profileUpdateForm": form}
    )

@login_required (login_url='login') 
def add_identity(request):
    user = request.user

    if request.method == "POST":
        identityForm = IdentityForm(request.POST, user= request.user )
        
        if identityForm.is_valid():
                new_identity = identityForm.save(commit=False)
                new_identity.linked_user = user
                new_identity.save()
                
                add_notification(user, "A new identity has been added!")

                messages.success(request, "Your new identity was successfully added!")
                return redirect("homepage")
            
    else:
        identityForm = IdentityForm(user=request.user)

    return render(
        request, 
        "htmlTemplates/AddIdentity.html",
        {
            "identity_form": identityForm,
            "context_form": ContextForm(),
        }
    )

@api_view(["POST"])
def create_context(request):

    context_name = request.data.get("context_name", "").strip()
    user = request.user

    if not context_name:
        return Response(
            {"success": False, "error": "Context name cannot be empty."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if Context.objects.filter(context_name=context_name).exists():
        return Response({
            "success": False,
            "error": "This context already exists."
        })

    new_context, created = Context.objects.get_or_create(
        context_name=context_name,
        linked_user=user
    )

    return Response({
        "success": True,
        "context_id": new_context.id,
        "context_name": new_context.context_name
    })


@login_required (login_url='login') 
def identity_management(request):
    user = request.user    
    identities = Identity.objects.filter(linked_user=user)
    serialized_identities = IdentitySerializer(identities, many=True).data
    contexts = Context.objects.filter(linked_user = user)

    #---Group by context---
    grouped_identities = defaultdict(list)

    #---get all unique contexts this user made---#
    unqiue_contexts = {contextObj.id: contextObj.context_name for contextObj in contexts}

    #---Each context id is linked to → a priority identity id (which is what this map has)---#
    priority_map = {contextObj.id: contextObj.priority_identity_id for contextObj in contexts}

    #----group identities by context_name-----#
    for identity in serialized_identities:
        context_id = identity['identity_context']
        context_name = unqiue_contexts.get(context_id, f"Context {context_id}")
        
        #---adding the priority flag------#
        identity["is_priority"] = identity["id"] == priority_map.get(context_id)

        grouped_identities[context_name].append(identity)

    #---converting to normal dict---#
    grouped_identities = dict(grouped_identities)  
    
    return render(
        request, 
        "htmlTemplates/identityManager.html",
        {"grouped_identities": grouped_identities}
    )

#----------_____________for identityView.html__________--------#
@login_required (login_url='login') 
def identity_view(request, identity_id):
    selected_identity = get_object_or_404(Identity, id=identity_id)

    return render(
        request, 
        "htmlTemplates/identityView.html",
        {"selected_identity": selected_identity}
    )

@login_required (login_url='login') 
def delete_identity(request, identity_id):
    user = request.user
    identity = get_object_or_404(Identity, id=identity_id, linked_user=user)

    if request.method == "POST":
        identity.delete()
        messages.success(request, f"Identity '{identity.identity_name}' has been deleted.")
        add_notification(user, f"You have just successfully deleted the identity '{identity.identity_name}'!")
        return redirect("identity_management")
        
    messages.error(request, f"Identity '{identity.identity_name}' was not successfully been deleted.")
    return redirect("identity_management")

#-----For the prioritize functionality: Prority identity for a specific context---#
@login_required (login_url='login') 
def prioritize_identity(request, identity_id):

    user = request.user
    identity = get_object_or_404(Identity, id=identity_id, linked_user=user)

    if not identity.identity_context:
            messages.error(request, "This identity has no context assigned.")
            return redirect("identity_management")

    try:
        #----remember, this is already refering to a Context obj---#
        selected_context = identity.identity_context
        selected_context.priority_identity = identity
        selected_context.save()

        add_notification(
            user,
            "You have just prioritized one of your identities!"
        )

        messages.success(
            request,
            f"Identity '{identity.identity_name}' has successfully been prioritized."
        )

    except DatabaseError:
        messages.error(
            request,
            "Something went wrong while prioritizing the identity."
        )

    return redirect("identity_management")


#----------_____________for editIdentity.html _____________________--------#
@login_required (login_url='login') 
def edit_identity(request, identity_id):
    user = request.user
    identity = get_object_or_404(Identity, id=identity_id, linked_user=user)

    if request.method == "POST":
        edit_identity_form = EditIdentityForm(request.POST, instance = identity, user = user )
        if edit_identity_form.is_valid():
            edit_identity_form.save()
            add_notification(
                request.user, 
                "You have just updated one of your identities!"
            )
            messages.success(
                request, 
                f"Identity '{identity.identity_name}' has successfully been updated."
            )

            return redirect("identity_management")

    else: 
        edit_identity_form = EditIdentityForm()

    return render(
        request, 
        "htmlTemplates/editIdentity.html",
        {"edit_identity_form": edit_identity_form}
    )


#---________------------------for clientManager.html-----------_________________-----#
@login_required (login_url='login') 
def client_management(request):
    user = request.user 
    clients = APIClient.objects.filter(linked_user = user)
    #---break it down to a list of dicts---#
    serialized_clients = APIClientSerializer(clients, many=True).data


    clients_list = [
        {
            "id": clientObj.id,
            "client_name": clientObj.client_name,
            "priority_identity": clientObj.priority_identity.identity_name if clientObj.priority_identity else None
        }
        for clientObj in clients
    ]

    return render(
        request, 
        "htmlTemplates/clientManager.html",
        {"clients_list": clients_list}
    )

#----_______________________The delete client function for clientManager.html_______________----#
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def api_delete_client(request, client_id):
    """
    This deletes the client based on the client_id input
    """
    user = request.user
    try: 
        selected_client = get_object_or_404(APIClient, id=client_id, linked_user = user)

    except APIClient.DoesNotExist():
        return Response({"error": "The targeted client could not be found."}, status=status.HTTP_404_NOT_FOUND)

    #---saving the client's name before deleting it----#s
    client_name = selected_client.client_name
    selected_client.delete()

    add_notification(user, f"You have successfuly deleted the Client '{client_name}'!" )

    return Response({"success": f"The Client '{client_name}' has been successfully deleted!"}, status=status.HTTP_200_OK )


#------------------__________________--For AddClient.html--------________________________---------------------------#
@login_required (login_url='login') 
def add_client(request):
    user = request.user

    if request.method == "POST":
        form = APIClientForm(request.POST, user=user)
        if form.is_valid():
            #---Connecting the linked user before saving---#
            client = form.save(commit=False)
            client.linked_user = user
            #--Setting up secure key----#
            client.api_key = secrets.token_hex(32)  
            
            client.save()

            add_notification(user, f"You have just set the client '{client.client_name}' to retreive only {client.priority_identity} ")

            messages.success(request, f"The New Client has been added successfully. \n Your Api key is {client.api_key}  !")
            return redirect("homepage")
             
    else:
        form = APIClientForm(user=user)

    return render(
        request, 
        "htmlTemplates/AddClient.html",
        {"client_form": form}
    )


#---------------For clientView.html------------#
@login_required (login_url='login') 
def client_view(request, client_id):
    client = get_object_or_404(APIClient, id=client_id, linked_user=request.user)
    
    return render(
        request, 
        "htmlTemplates/clientView.html", 
        {"selected_client": client }
    )

#----for the delete button in clientView.html------#
@login_required (login_url='login') 
def delete_client(request, client_id):
    user = request.user
    client = get_object_or_404(APIClient, id=client_id, linked_user = user)
    if request.method == "POST":
        client.delete()
        messages.success(request, f"The Client '{client.client_name}' was successfully deleted!")
        add_notification(user,  f"The Client '{client.client_name}' was deleted")

    else: 
        messages.error(request, f"Failed to delete the Client '{client.client_name}'!")

    return redirect("client_management")



#---------------For EditClient.html------------#
@login_required (login_url='login') 
def edit_client(request, client_id):
    client = get_object_or_404(APIClient, id=client_id, linked_user=request.user)

    if request.method == "POST":
        form = EditAPIClientForm(request.POST, instance=client, user=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, "Client updated successfully!")

            add_notification(request.user, f"You have just updated your client {client}!")
            return redirect("client_management")
        
    else:
        form = EditAPIClientForm(instance=client, user=request.user)

    return render(
        request, 
        "htmlTemplates/EditClient.html", 
        {"edit_Client_Form": form}
    )


#-------_________-------For ApiTesting.html--------_________-----#
@login_required (login_url='login') 
def api_testing(request):
    user = request.user
    all_contexts = Context.objects.filter(linked_user = user)

    return render(
        request, 
        "htmlTemplates/ApiTesting.html",
        {"context_list": all_contexts}
    )

#------------api functions used in ApiTesting.html----------------# 
@api_view(["GET"])
def get_identity_with_context(request, context_id):
    user = request.user

    email = request.GET.get("email")

    #---For when the user get redirected to ApiTesting.html----#
    pending_contextID_key = request.session.get("pending_contextID_key")

    if not email and pending_contextID_key == None :
        return Response({"error": "Email is required"}, status=400)

    #----get user from using the input email---#
    if(pending_contextID_key != None):
        selected_context = get_object_or_404(Context, linked_user = user, id = pending_contextID_key)
        user = selected_context.linked_user
    else: 
        try:

            user = get_object_or_404(User, email=email)

        except User.DoesNotExist: 
            return Response({
                    "error": "No user linked to that email was found",
                }, 
                status=404
            )

    #-----this means verification was not done
    if(pending_contextID_key ==None):
        try:
            selected_context = get_object_or_404(Context, linked_user = user, id = context_id)
        except Context.DoesNotExist:
            return Response({"error": "Context not found"}, status=404)

    #---Get the prioritized identity linked to this context----#

    identity = selected_context.priority_identity


    if(identity):
        retrieved_identity_name = identity.identity_name
        retrieved_identity_context = identity.identity_context.context_name
        retrieved_identity_info = identity.related_info 

    
    else: 
        #--fallback for no priority: return the first identity linked to this context
        identity = selected_context.identity_set.first() if selected_context.identity_set.exists() else None
        retrieved_identity_name = selected_context.identity_set.first().identity_name if selected_context.identity_set.exists() else "No identity was found for this context"
        retrieved_identity_context = selected_context.identity_set.first().identity_context.context_name if selected_context.identity_set.exists() else "404"
        retrieved_identity_info = selected_context.identity_set.first().related_info if selected_context.identity_set.exists() else " No additional information was found!"

    #----store + check for security level----------#
    if(identity != None):
        security = identity.security_level
        #---for if the security level is higher than low---#
        if(security != "low" and pending_contextID_key == None):
            request.session["pending_contextID_key"] = context_id
            security_response = securityVerifications(request, user, security, selected_context)

            #---for high security cases----#
            if security_response:
                return security_response
        
        
        add_notification(user, f"Your identity '{identity.identity_name}' was retreived!")

    
    #---remove the pending context key----#
    if request.session.get("pending_contextID_key"):
        request.session.pop("pending_contextID_key", None)

    return Response({
        "identity_name": retrieved_identity_name,
        "context": retrieved_identity_context,
        "related_info": retrieved_identity_info
    })


@api_view(["GET"])
def get_api_identity(request):
    api_key = request.GET.get("api_key")    
    pending_api_key = request.session.get("pending_api_key")

    if not api_key:
        return Response({"error": "API key is required"}, status=400)
    
    try: 
        client = APIClient.objects.get(api_key=api_key)
    except APIClient.DoesNotExist:
        return Response({"error": "Invalid API key"}, status=403)
    #----Now we can trust this request-----#

    #---Get the user---#
    targeted_user = client.linked_user

    #------Get identity---#
    identity = client.priority_identity

    #---in case no identity was set for this user----#
    if not identity:
        return Response({
            "error": "No identity was set for this client"
        }, status=404)

    #----store + check for security level----------#
    security = identity.security_level

    #---for if the security level is higher than low---#
    if(security != "low" and pending_api_key == None):
        request.session["pending_api_key"] = api_key
        security_response = securityVerifications(request, targeted_user, security, client)
        #---for high security cases----#
        if security_response:
            return security_response

    add_notification(targeted_user, f"Your identity '{identity.identity_name}' was retreived!")

    #---remove the pending api key----#
    if request.session.get("pending_api_key"):
        request.session.pop("pending_api_key", None)

    if identity:
        return Response({
            "identity_name": identity.identity_name,
            "context": identity.identity_context.context_name,
            "related_info": identity.related_info            
        })
    
    return Response({
        "error": "No identity was set for this client"
    }, status=404)


#---for the handling the security levels in identitie when they are requested for in ApiTesting.html---#
def securityVerifications(request, targeted_user, security_level, requestModel):

    #----high= always need OTP-----------#
    if(security_level== "high"):
        otp_generation(request, targeted_user, "api_access")
        return Response({
            "requires_verification": True,
            "message": "OTP Required (High Security)"
        })

    if(security_level== "medium"):
        verified = request.session.get("api_verified", False)
        
        if request.user not in requestModel.verified_users.all():
            otp_generation(request, targeted_user, "api_access")
            return Response({
                "requires_verification": True,
                "message": "OTP Required (Medium Security)"
            })
        
    return None 


#----------______________________For the notifications__________________----------------#
@login_required (login_url='login') #---Ensure the user is logged in--#
def notifications_page(request):

    #---Mark updates as read---#
    UserNotifications.objects.filter(
        user=request.user,
        is_read=False
        ).update(is_read=True)

    #---the num of rows on display in the notifications play
    rowCount = 20

    notificationsList = UserNotifications.objects.filter(
        user= request.user.id
        ).order_by('-created_date')[:rowCount]
    

    return render(
        request, 
        "htmlTemplates/notificationsPage.html",
        {'notification_list': notificationsList}
    )


def add_notification(selected_user, content):
    """
    This adds in a new notification for a given user.
    `selected_user` is the user object.
    `content` is the notification text.
    """

    serializer = NotificationsSerializer(data={
        "user": selected_user.id,  #---Note to self that DRF serializers accept PK for ForeignKey----#
        "notification_content": content
    })

    #----Validate and save the data-------#
    if serializer.is_valid():
        serializer.save()
        return serializer.data  #---Returns the saved notification as dict---#
    
    else:
        #---keep for debugging---#
        print("Error encountered when creating notification: ", serializer.errors)
        return None


#----for the notification bell that auto calls every 10s/when the page reloads---#
def check_for_new_notifications(request):

    """Check if the logged-in teacher has new status updates."""
    user = request.user

    #----Check if there are new notifications for this logged in user----#
    new_updates = UserNotifications.objects.filter(user=user.id, is_read=False).exists()
    if(new_updates):
        num_of_notifications= len(UserNotifications.objects.filter(user=user.id, is_read=False))
    else:
        num_of_notifications= 0

    return JsonResponse({"has_new_updates": new_updates, "notification_count": num_of_notifications})










