from rest_framework import viewsets, status
from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from service.authentication.node_basic import NodeBasicAuthentication
from service.authors.serializers import AuthorSerializer, AuthorURLSerializer
from social.app.models.author import Author


class AuthorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows for the retrieval and modification of Authors.
    """

    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = (IsAuthenticated,)

    @detail_route(methods=["GET"], authentication_classes=(NodeBasicAuthentication,))
    def author_friends(self, request, pk=None):
        """
        Returns a (possibly empty) list of  Authors that are friends with the user specified by id.
        
        Example successful response:
        
            {
                "query":"friends",
                "authors":[
                    "http://host3/author/de305d54-75b4-431b-adb2-eb6b9e546013",
                    "http://host2/author/ae345d54-75b4-431b-adb2-fb6b9e547891"
                ]
            }
        
        Example failed response:
        
            {
                "detail": "Author not found."
            }
        """
        try:
            friends = self.get_object().friends.all()
        except Author.DoesNotExist:
            return Response(
                {'detail': 'Author not found.'},
                status=status.HTTP_404_NOT_FOUND)

        return Response(
            {"query": "friends",
             "authors": AuthorURLSerializer(friends, context={'request': request}, many=True).data},
            status=status.HTTP_200_OK)

    def two_authors_are_friends(request, local_id=None, other_host_name=None, other_id=None):
        """
        Returns true if these two authors are found, and 
        """
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)
