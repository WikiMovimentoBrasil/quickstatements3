from django.contrib.auth.models import User

from .models import Token
from api.client import Client


def user_from_token(token):
    client = Client.from_token(token)

    # Verify submitted token by checking `username` in the response
    wikimedia_username = client.get_username()

    user, was_created = User.objects.get_or_create(
        username=wikimedia_username,
    )

    if not was_created:
        Token.objects.filter(user__id=user.id).delete()

    Token.objects.create(user=user, value=token)

    return user


def clear_tokens(user):
    Token.objects.filter(user__id=user.id).delete()
