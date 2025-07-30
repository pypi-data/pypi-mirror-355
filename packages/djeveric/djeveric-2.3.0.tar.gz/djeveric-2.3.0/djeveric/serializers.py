from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class ConfirmationSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate_token(self, value):
        if not self.instance.check_confirmation_token(value):
            raise ValidationError("Invalid token")
        return value
