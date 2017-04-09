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


# /service/author/{id} (overrides other 2 as well if they aren't defined)
class AuthorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows for the retrieval and modification of Authors that exist.

    Example success response:
    <pre>
    {
        &nbsp&nbsp&nbsp"id": "http://127.0.0.1:8000/service/author/447c20fd-6fe2-4ea5-a9f7-2edabe2cc92c/",
        &nbsp&nbsp&nbsp"host": "http://127.0.0.1:8000/service/",
        &nbsp&nbsp&nbsp"displayName": "Test User",
        &nbsp&nbsp&nbsp"url": "http://127.0.0.1:8000/service/author/447c20fd-6fe2-4ea5-a9f7-2edabe2cc92c/",
        &nbsp&nbsp&nbsp"friends": [
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp{
                 &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"url": "http://127.0.0.1:8000/service/author/90926f84-1672-4f0f-873e-f2f720ae28f2/"
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp}
        &nbsp&nbsp&nbsp],
        &nbsp&nbsp&nbsp"github": "https://github.com/tester",
        &nbsp&nbsp&nbsp"firstName": "Test",
        &nbsp&nbsp&nbsp"lastName": "User",
        &nbsp&nbsp&nbsp"email": "test@ualberta.ca",
        &nbsp&nbsp&nbsp"bio": "I am a tester."
    }
    </pre>

    Example failure response:
    <pre>
    {
        &nbsp&nbsp&nbsp"detail": "Not found."
    }
    </pre>
    """

    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    authentication_classes = (NodeBasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    # /service/author/{id}/friends
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

        author_urls = AuthorURLSerializer(friends, context={'request': request}, many=True).data
        return Response({
            "query": "friends",
            "authors": [
                author_url['url'] for author_url in author_urls
            ]
        }, status=status.HTTP_200_OK)

    # /service/author/{local_id}/friends/{other_host_name}/author/{other_id}
    @detail_route(methods=["GET"], authentication_classes=(NodeBasicAuthentication,))
    def two_authors_are_friends(self, request, local_id=None, other_host_name=None, other_id=None):
        """
        Allows for seeing whether or not two authors on potentially different hosts are friends.

        Example success query:

            {
                "query":"friends",
                "authors":[
                    "http://127.0.0.1:5454/author/de305d54-75b4-431b-adb2-eb6b9e546013",
                    "http://127.0.0.1:5454/author/ae345d54-75b4-431b-adb2-fb6b9e547891"
                ],
                "friends": true
            }
        """
        try:
            local_author = Author.objects.get(id=local_id)
        except ObjectDoesNotExist, e:
            return Response({
                "query": "friends",
                "error": "Author %s does not exist" % str(local_id),
                "status": status.HTTP_404_NOT_FOUND,
            }, status.HTTP_404_NOT_FOUND)

        # Verify the friendship on our end
        is_friendship_record = Author.friends.through.objects.filter(
            from_author_id=local_id,
            to_author_id=other_id).exists()
        # Verify the requested to_author matches the given other_host_name
        is_remote_author_record = Author.objects.filter(id=other_id, node__host=other_host_name).exists()

        is_friends = is_friendship_record and is_remote_author_record

        return Response({
            "query": "friends",
            "authors": [
                local_author.get_uri(),
                Author.get_uri_from_host_and_uuid(other_host_name, other_id)
            ],
            "friends": is_friends,
        })
