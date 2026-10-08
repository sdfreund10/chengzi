from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False, style={"input_type": "password"})

    def validate_email(self, value: str) -> str:
        # Store/lookup emails in lowercase so unique=True is case-safe.
        return value.strip().lower()
