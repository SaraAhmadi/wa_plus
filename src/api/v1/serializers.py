from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.db import transaction
from apps.user_management.models import User, Role, Permission


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(),
        many=True,
        write_only=True,
        source='permissions',
        required=False
    )

    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permissions', 'permission_ids', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        permission_ids = validated_data.pop('permissions', None)
        with transaction.atomic():
            role = Role.objects.create(**validated_data)
            if permission_ids is not None:
                role.permissions.set(permission_ids)
        return role

    def update(self, instance, validated_data):
        permission_ids = validated_data.pop('permissions', None)
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if permission_ids is not None:
                instance.permissions.set(permission_ids)
        return instance


class UserSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(many=True, read_only=True)
    role_ids = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        many=True,
        write_only=True,
        source='roles',
        required=False
    )
    password = serializers.CharField(
        write_only=True,
        required=False,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'full_name', 'is_active',
            'is_superuser', 'is_staff', 'password', 'roles', 'role_ids',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['is_superuser', 'is_staff', 'created_at', 'updated_at']
        extra_kwargs = {
            'email': {'required': True},
            # Ensure password is not sent in response, already handled by write_only=True
            # 'password': {'write_only': True}
        }

    def create(self, validated_data):
        role_ids = validated_data.pop('roles', None)
        password = validated_data.pop('password', None)

        with transaction.atomic():
            # create_user handles password hashing and saving
            user = User.objects.create_user(password=password, **validated_data)

            if role_ids is not None:
                user.roles.set(role_ids)
        return user

    def update(self, instance, validated_data):
        role_ids = validated_data.pop('roles', None)
        password = validated_data.pop('password', None)

        with transaction.atomic():
            if password:
                instance.set_password(password) # set_password handles hashing

            # Update other fields
            instance = super().update(instance, validated_data)
            # No need to call instance.save() here as super().update() does it.

            if role_ids is not None:
                instance.roles.set(role_ids)
        return instance


class TokenSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    token_type = serializers.CharField()
