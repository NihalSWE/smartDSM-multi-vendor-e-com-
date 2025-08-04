from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class PhoneOrEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = None

        # Try phone number
        try:
            user = User.objects.get(phone_number=username)
        except User.DoesNotExist:
            # Try email only if it looks like an email
            if '@' in username:
                try:
                    user = User.objects.get(email=username)
                except User.DoesNotExist:
                    return None

        if user and user.check_password(password):
            return user

        return None