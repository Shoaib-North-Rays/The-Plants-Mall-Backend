from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from Authentication.models import *
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
import random
from .serializers import RegisterSerializer,LoginSerializer 
from rest_framework import  permissions
User = get_user_model()

class RegisterView(APIView):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    # Create user
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered. Check email for verification code."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Update user
    def put(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = RegisterSerializer(user, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User updated successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = RegisterSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User partially updated successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Delete user
    def delete(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        user.delete()
        return Response({"message": "User deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

class VerifyEmailView(APIView):
    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")

        try:
            user = User.objects.get(email=email)
            
            code_obj = VerificationCode.objects.get(user=user, code=code, is_used=False)
         
        except:
            return Response({"error": "Invalid username or code"}, status=status.HTTP_400_BAD_REQUEST)

        
        code_obj.is_used = True
        code_obj.save()
        user.is_active = True
        user.save()
       
        if code_obj.use_for=="registration":
            VerificationCode.objects.filter(user=user, is_used=True,code=code).delete()
           
        
        return Response({"message": "Email verified successfully"}, status=status.HTTP_200_OK)
class ResendVerificationCodeView(APIView):
    def post(self, request):
        email = request.data.get("email")
        use_for=request.data.get("use_for")

        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        
        VerificationCode.objects.filter(user=user, is_used=False,use_for=use_for).delete()
        code=random.randint(100000, 999999)
         
        VerificationCode.objects.create(user=user,code=code,use_for=use_for)

        
        subject = "Verify Your Account"
        from_email = settings.EMAIL_HOST_USER
        to = [user.email]
        html_content = render_to_string(
        "emails/verification_email.html",
        {"code": code, "username": user.username}
    )

 
        msg = EmailMultiAlternatives(subject, "", from_email, to)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        return Response({"message": "New verification code sent to your email."}, status=status.HTTP_200_OK)


class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "name": user.name,
                "phone": user.phone,
            }
        }, status=status.HTTP_200_OK)
class ForgotPasswordView(APIView):
    def post(self, request):
        identifier = request.data.get("email")
        if not identifier:
            return Response({"error": "Email or username is required"}, status=400)

        try:
            if "@" in identifier:
                user = User.objects.get(email=identifier)
            else:
                user = User.objects.get(username=identifier)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
        code=random.randint(100000, 999999)
         
        VerificationCode.objects.create(user=user,code=code,use_for="password_reset")

        
        subject = "Verify Your Account"
        from_email = settings.EMAIL_HOST_USER
        to = [user.email]
        html_content = render_to_string(
        "emails/verification_email.html",
        {"code": code, "username": user.username}
    )

 
        msg = EmailMultiAlternatives(subject, "", from_email, to)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

         

        return Response({"message": "Password reset verification code sent to your email"})
class ResetPasswordView(APIView):
    def post(self, request):
        email=request.data.get("email")
        new_password = request.data.get("new_password")

        if not email or  not new_password:
            return Response({"error": "email and new_password are required"}, status=400)

        try:
            
            user = User.objects.get(email=email)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response({"error": "User not found!"}, status=400)
        try:
            
            code_obj = VerificationCode.objects.get(user=user,is_used=True,use_for="password_reset")
        except (VerificationCode.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response({"error": "Code not found!"}, status=400)
         
        user.set_password(new_password)
        user.save()
        code_obj.delete()

        return Response({"message": "Password reset successful"})


 