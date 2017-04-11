from rest_framework.authentication import SessionAuthentication


class AuthorSessionAuthentication(SessionAuthentication):
    """
    Subset of session authentication that prevents the API user from using our internal APIs.
    """
    def authenticate(self, request):
        return_value = super(AuthorSessionAuthentication, self).authenticate(request)

        # Make sure this User has an associated Author (i.e. they're not the API docs User)
        if return_value and not return_value[0].profile:
            return None

        return return_value
