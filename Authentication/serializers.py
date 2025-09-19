from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from rest_framework.exceptions import AuthenticationFailed
from Authentication.models import  *
import random
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "password", "email", "name", "phone", "role","profile_pic"]

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data, is_active=True)

 
    #     code = f"{random.randint(100000, 999999)}"
    #     VerificationCode.objects.create(user=user, code=code,use_for="registration")

 
    #     subject = "Verify Your Account"
    #     from_email = settings.EMAIL_HOST_USER
    #     to = [user.email]
    #     html_content = render_to_string(
    #     "emails/verification_email.html",
    #     {"code": code, "username": user.username}
    # )

 
    #     msg = EmailMultiAlternatives(subject, "", from_email, to)
    #     msg.attach_alternative(html_content, "text/html")
    #     msg.send()
        return user
    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)

        instance.save()
        return instance
class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()   
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        identifier = attrs.get("identifier")
        password = attrs.get("password")

        user = None

         
        if "@" in identifier:
            try:
                user_obj = User.objects.get(email=identifier)
                username = user_obj.username
                user = authenticate(username=username, password=password)
            except User.DoesNotExist:
                raise AuthenticationFailed("Invalid email or password")
        else:
             
            user = authenticate(username=identifier, password=password)

        if not user:
            raise AuthenticationFailed("Invalid credentials")

        if not user.is_active:
            raise AuthenticationFailed("Account is disabled")

        attrs["user"] = user
        return attrs
