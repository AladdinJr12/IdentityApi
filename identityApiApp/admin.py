from django.contrib import admin

from .models import *

#----putting identity model in admin view---#
#---- Identity admin ----#
@admin.register(Identity)
class IdentityAdmin(admin.ModelAdmin):
    list_display = ("identity_name", "security_level", "visibility", "identity_context")


#---- Context admin ----#
@admin.register(Context)
class ContextAdmin(admin.ModelAdmin):
    list_display = ("context_name",)



#---------------------------------------------------------------#


