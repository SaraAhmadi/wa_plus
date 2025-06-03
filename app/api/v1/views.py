from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from .models import User, Role, Permission
from .permissions import HasPermission, IsOwnerOrAdmin
from .serializers import UserSerializer, RoleSerializer, PermissionSerializer, TokenSerializer
from rest_framework_simplejwt.views import TokenObtainPairView as BaseTokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as BaseTokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.db.models import Q # For OR queries


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().prefetch_related('roles__permissions').order_by('id')
    serializer_class = UserSerializer
    # Default permission_classes, will be overridden by get_permissions

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [AllowAny]
        elif self.action == 'list':
            self.permission_classes = [IsAdminUser]
        elif self.action in ['retrieve', 'update', 'partial_update']:
            # IsOwnerOrAdmin will be checked for object-level permission.
            # IsAuthenticated ensures the user is logged in.
            self.permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
        elif self.action == 'destroy':
            self.permission_classes = [IsAdminUser]
        else:
            # Default to IsAuthenticated if no specific action matches
            self.permission_classes = [IsAuthenticated]
        return [permission() for permission in self.permission_classes]

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='me')
    def get_current_user_details(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all().prefetch_related('permissions').order_by('id')
    serializer_class = RoleSerializer
    permission_classes = [IsAdminUser] # Only admins can manage roles

class PermissionViewSet(viewsets.ModelViewSet):
    queryset = Permission.objects.all().order_by('id')
    serializer_class = PermissionSerializer
    permission_classes = [IsAdminUser] # Only admins can manage permissions


class CustomTokenObtainPairSerializer(BaseTokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims here if needed
        # token['username'] = user.username
        return token

    def validate(self, attrs):
        # The 'username_field' for User model is 'email'.
        # However, we want to allow login with either email or actual username.
        identifier = attrs.get(self.username_field) # This will fetch 'email' field from form
        password = attrs.get('password')

        user = None
        request = self.context.get('request')

        # Try to authenticate with the identifier as email
        authenticated_user_by_email = authenticate(request=request, username=identifier, password=password)

        if authenticated_user_by_email:
            user = authenticated_user_by_email
        else:
            # If email auth failed, try to find user by username field, then authenticate with their email
            try:
                user_obj_by_username = User.objects.get(username=identifier)
                # Now authenticate using the email of this user (since USERNAME_FIELD is email)
                authenticated_user_by_username_lookup = authenticate(request=request, username=user_obj_by_username.email, password=password)
                if authenticated_user_by_username_lookup:
                    user = authenticated_user_by_username_lookup
            except User.DoesNotExist:
                pass # User with this username does not exist

        if not user or not user.is_active:
            raise serializers.ValidationError(
                {"detail": "No active account found with the given credentials"},
                code='authentication_failed'
            )

        self.user = user # Important for super().validate() or get_token()

        # Original super().validate(attrs) would re-authenticate.
        # We've already authenticated. Now, just get the token data.
        refresh = self.get_token(self.user)
        data = {}
        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)

        # Add custom data to response if needed from TokenSerializer
        # if api_settings.UPDATE_LAST_LOGIN:
        #     update_last_login(None, self.user)

        return data

class CustomTokenObtainPairView(BaseTokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
