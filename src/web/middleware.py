from django.conf import settings
from django.utils import translation

from web.models import Preferences


def language_cookie_middleware(get_response):
    def middleware(request):
        if request.user.is_authenticated:
            language = Preferences.objects.get_language(
                request.user, settings.LANGUAGE_CODE
            )
        else:
            language = settings.LANGUAGE_CODE

        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()

        response = get_response(request)
        return response

    return middleware
