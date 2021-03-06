from django.shortcuts import redirect
from django.urls import reverse
from django.utils.encoding import iri_to_uri

from social.app.models.author import Author


class AuthRequiredMiddleware(object):
    """
    Forces a redirect to the login on all restricted pages.

    Forces a redirect to the home page on accessing the sign-up page while authenticated.
    """

    def process_request(self, request):
        path = request.path_info.lstrip('/')
        if request.user.is_authenticated():
            if any(path == eu for eu in ["accounts/register/"]):
                return redirect(reverse('app:index'))

            # Redirect server admins to the admin app
            if request.user.is_staff:
                if not path.startswith('admin') and not path.startswith('service'):
                    return redirect(reverse('admin:index'))
            elif request.user.username == "api":
                if not path.startswith('service') and not path.startswith('logout'):
                    return redirect(reverse('docs'))
            else:
                user_profile = Author.objects.get(user_id=request.user.id)
                if not user_profile.activated:
                    # Redirect users that haven't been approved by the server admin
                    if not path.startswith('admin') and not path.startswith('service') and \
                            not any(path == eu for eu in ["logout/",
                                                          iri_to_uri(reverse('activation_required', args=[])).lstrip(
                                                              '/')]):
                        return redirect(reverse('activation_required', args=[]))
        return None
