from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import *

urlpatterns = [
  path('dashboard_stats/',DashboardStatsAPIView.as_view(),name="dashboard_stats"),
  path('dispatchers/',DispatcherListAPIView.as_view(),name="dispatchers"),
  path("staff-users/", StaffUsersAPIView.as_view(), name="staff-users"),
]
