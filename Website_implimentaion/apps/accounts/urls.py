from django.urls import path
from . import views

urlpatterns = [
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),
    path('login/otp', views.otp_login_view, name='login_otp'),
    path('forgot/password', views.forgot_password_view, name='forgot_password'),
    path('reset/password/<str:token>', views.reset_password_view, name='reset_password'),
    path('profile', views.profile_view, name='profile'),
    path('profile/email', views.profile_email_view, name='profile_email'),
]
