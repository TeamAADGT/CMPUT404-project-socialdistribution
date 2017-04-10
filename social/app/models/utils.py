import uuid

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator


def is_valid_uuid(uuid_test):
    try:
        uuid.UUID(uuid_test)
    except:
        return False

    return True


def is_valid_url(url):
    val = URLValidator()
    try:
        val(url)
        return True
    except ValidationError as e:
        return False
