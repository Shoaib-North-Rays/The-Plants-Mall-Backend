from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import *

urlpatterns = [
   path('register/',RegisterView.as_view(), name='register'),
   path('verify-email/',VerifyEmailView.as_view(),name="verify-email"),
   path('resend-code/',ResendVerificationCodeView.as_view(),name="verify-email"),
   path("login/", LoginAPIView.as_view(), name="login"),
   path('forgot-password/',ForgotPasswordView.as_view(),name="reset-password"),
   path('reset-password/',ResetPasswordView.as_view(),name="reset-password"),
   path("user/<int:pk>/", RegisterView.as_view()),
]
