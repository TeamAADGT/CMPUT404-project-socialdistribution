import uuid


def is_valid_uuid(uuid_test):
    try:
        uuid.UUID(uuid_test)
    except:
        return False

    return True
