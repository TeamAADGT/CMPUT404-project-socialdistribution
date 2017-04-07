import uuid

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import viewsets, status, generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from service.authentication.node_basic import NodeBasicAuthentication
from service.authors.serializers import AuthorSerializer, AuthorURLSerializer
from social.app.models.author import Author


class AuthorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows for the retrieval and modification of Authors.
    """

    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    authentication_classes = (NodeBasicAuthentication,)
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


class AuthorFriendship(APIView):
    authentication_classes = (NodeBasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, me=None, other_host=None, you=None):
        author_friends_queryset = Author.friends.through.objects.filter(
            from_author_id=me)

        # Verify that the first uuid exists
        if len(author_friends_queryset) == 0:
            return Response({
                "query": "friends",
                "error": "Author %s does not exist" % str(me),
                "status": 404,
            }, 404)

        friendship_record = author_friends_queryset.filter(
            from_author_id=me,
            to_author_id=you)

        is_friends = False
        authors = {Author.objects.get(id=me).get_uri()}

        # Verify and add the second uuid
        if len(friendship_record) == 1:
            is_friends = True
            authors.add(Author.objects.get(id=you).get_uri())

        return Response({
            "query": "friends",
            "authors": authors,
            "friends": is_friends,
        })
