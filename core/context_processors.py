from django.utils import translation

def language_code(request):
    return {
        'LANGUAGE_CODE': translation.get_language()
    }
