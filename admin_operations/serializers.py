from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class DispatcherSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email", "phone", "is_active","last_activity"]

class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name","username","profile_pic", "email","phone", "role","last_activity","is_active"]
