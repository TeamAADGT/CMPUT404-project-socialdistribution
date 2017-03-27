import os

from rest_framework.authentication import BasicAuthentication
from rest_framework.exceptions import AuthenticationFailed

from social.app.models.node import Node


class NodeBasicAuthentication(BasicAuthentication):
    """
    Source: http://www.django-rest-framework.org/api-guide/authentication/#custom-authentication
    and https://github.com/tomchristie/django-rest-framework/blob/master/rest_framework/authentication.py
    
    Set up the keys in Heroku via this process: 
    https://devcenter.heroku.com/articles/config-vars#setting-up-config-vars-for-a-deployed-application
    """

    def __init__(self):
        self.node = None

    def authenticate(self, request):
        host = request.META["REMOTE_HOST"] or request.META["REMOTE_ADDR"]

        if (host == '127.0.0.1' or host == 'localhost') and request.META["SERVER_PORT"] != "80":
            # For local testing purposes
            host = "%s:%s" % (host, request.META["SERVER_PORT"])

        try:
            self.node = Node.objects.get(host=host)
        except Node.DoesNotExist:
            # Request doesn't match a known node -- failed
            raise AuthenticationFailed("Request comes from unknown remote server.")

        if not self.node.requires_auth:
            return self.node, None
        return super(NodeBasicAuthentication, self).authenticate(request)

    def authenticate_credentials(self, userid, password):
        try:
            incoming_node = Node.objects.get(
                host=self.node.host,
                incoming_username=userid, incoming_password=password)
            return self.node, None
        except Node.DoesNotExist:
            raise AuthenticationFailed("Invalid username/password.")
