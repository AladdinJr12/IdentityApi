from django.urls import include, path
from . import views #--Importing from views.py--//

from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns =[
    path ('', views.index, name='index' ),
    path ('sign-up/', views.signup, name='sign-up' ),
    path ('login/', views.login_view, name='login' ),
    path ('logout/', views.user_logout, name='logout' ),
    path ('resend-otp/', views.resend_otp, name='resend_otp' ),
    path ('forget-password/', views.forget_password, name='forget_password' ),
    path ('reset-password/', views.reset_password, name='reset_password' ),
    path ('auth-reset-password/', views.auth_reset_password, name='auth_reset_password' ),
    path ('homepage/', views.homepage, name='homepage' ),
    path ('identity-management/', views.identity_management, name='identity_management'),
     path('identity-view/<int:identity_id>/', views.identity_view, name='identity_view'),
    path ('profile-page/', views.profile_page, name='profile_page'),
    path ('update-profile/', views.update_profile, name='update_profile'),
    path ('add-identity/', views.add_identity, name='add_identity'),
    path ('delete-identity/<int:identity_id>/', views.delete_identity, name='delete_identity'),
    path ('edit-identity/<int:identity_id>/', views.edit_identity, name='edit_identity'),
    path ('prioritize-identity/<int:identity_id>/', views.prioritize_identity, name='prioritize_identity'),
    path ('verification-page/', views.verification_page, name='verification_page' ),
    path ('notifications/', views.notifications_page, name='notifications' ),
    path ('check-for-new-notifications/', views.check_for_new_notifications, name='check_for_new_notifications' ),
    path ('add-client/', views.add_client, name='add_client'),
    path('client-view/<int:client_id>/', views.client_view, name='client_view'),
    path ('edit-client/<int:client_id>/', views.edit_client, name='edit_client'),
    path ('delete-client/<int:client_id>/', views.delete_client, name='delete_client'),
    path ('client-management/', views.client_management, name='client_management'),
    path ('api-testing/', views.api_testing, name='api_testing'),

    #----Paths that uses api_view-----#
    path ('api/create-context/', views.create_context, name='api_create_context'),
    path ('api/get-identity/<str:context_id>/', views.get_identity_with_context, name='api_get_identity_with_context'),
    path ('api/delete-client/<int:client_id>/', views.api_delete_client, name='api_delete_client'),
    path ('api/get-client/', views.get_api_identity, name='get_api_identity'),

    #---Swagger documentation endpoints---#
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]