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

    def authenticate_credentials(self, userid, password):
        try:
            incoming_node = Node.objects.get(
                incoming_username=userid, incoming_password=password)
            return incoming_node, None
        except Node.DoesNotExist:
            raise AuthenticationFailed("Invalid username/password.")
