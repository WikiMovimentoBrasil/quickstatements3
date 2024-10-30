from django.conf import settings
from django.utils import translation

from web.models import Preferences


def language_cookie_middleware(get_response):
    def middleware(request):
        language = None

        if request.user.is_authenticated and settings.LANGUAGE_COOKIE_NAME not in request.COOKIES:
            language = Preferences.objects.get_language(request.user, "en")
            translation.activate(language)
            request.LANGUAGE_CODE = translation.get_language()

        response = get_response(request)

        if language:
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language)

        return response

    return middleware
