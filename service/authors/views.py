import logging
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import viewsets, status
from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from service.authentication.node_basic import NodeBasicAuthentication
from service.authors.serializers import AuthorSerializer, AuthorURLSerializer
from social.app.models.author import Author
from social.app.models.utils import is_valid_uuid


# /service/author/{id} (overrides other 2 as well if they aren't defined)
class AuthorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows for the retrieval and modification of Authors that exist.

    Example successful response:
    <pre>
    {
        "id": "http://127.0.0.1:8000/service/author/447c20fd-6fe2-4ea5-a9f7-2edabe2cc92c/",
        "host": "http://127.0.0.1:8000/service/",
        "displayName": "Test User",
        "url": "http://127.0.0.1:8000/service/author/447c20fd-6fe2-4ea5-a9f7-2edabe2cc92c/",
        "friends": [
            {
                 "url": "http://127.0.0.1:8000/service/author/90926f84-1672-4f0f-873e-f2f720ae28f2/"
            }
        ],
        "github": "https://github.com/tester",
        "firstName": "Test",
        "lastName": "User",
        "email": "test@ualberta.ca",
        "bio": "I am a tester."
    }
    </pre>
    """

    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    authentication_classes = (NodeBasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    # /service/author/{id}/friends (GET)
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

    # /service/author/{id}/friends (POST)
    @detail_route(methods=["POST"], authentication_classes=(NodeBasicAuthentication,))
    def author_friends_search(self, request, pk=None):
        """
        Returns a (possibly empty) list of Authors that are friends with the 
        user specified by id. The list of authors returned is bounded by the 
        supplied list of authors; only provided authors that are friends with 
        the given author are returned in the response.

        Example successful response:

            {
                "query":"friends",
                "author":"<authorid>"
                "authors":[
                    "http://host3/author/de305d54-75b4-431b-adb2-eb6b9e546013",
                    "http://host2/author/ae345d54-75b4-431b-adb2-fb6b9e547891"
                ]
            }
        
        """

        # Verify the request POST data to the specification requirements

        if 'query' not in self.request.data:
            return Response({
                'query': 'Missing query key!',
                'status': status.HTTP_422_UNPROCESSABLE_ENTITY
            }, status.HTTP_422_UNPROCESSABLE_ENTITY)
        elif self.request.data['query'] != 'friends':
            return Response({
                'query': 'Expected a query key of \'friends\'',
                'status': status.HTTP_422_UNPROCESSABLE_ENTITY
            }, status.HTTP_422_UNPROCESSABLE_ENTITY)

        if 'author' not in self.request.data:
            return Response({
                'author': 'Missing author key!',
                'status': status.HTTP_422_UNPROCESSABLE_ENTITY
            }, status.HTTP_422_UNPROCESSABLE_ENTITY)

        author_from_uuid = self.request.data['author']

        if is_valid_uuid(author_from_uuid) is False:
            return Response({
                'author': 'The author identifier is not a valid uuid4 value!',
                'status': status.HTTP_422_UNPROCESSABLE_ENTITY
            }, status.HTTP_422_UNPROCESSABLE_ENTITY)

        if author_from_uuid != pk:
            return Response({
                'author': 'The supplied author identifier does not match the identifier specified in the URL!',
                'status': status.HTTP_422_UNPROCESSABLE_ENTITY
            }, status.HTTP_422_UNPROCESSABLE_ENTITY)

        authors_to_find = self.request.data['authors']

        if 'authors' not in self.request.data:
            return Response({
                'authors': 'Missing authors key!',
                'status': status.HTTP_422_UNPROCESSABLE_ENTITY
            }, status.HTTP_422_UNPROCESSABLE_ENTITY)
        elif isinstance(authors_to_find, list) is False:
            return Response({
                'authors': 'The authors value must be a list of author URLs',
                'status': status.HTTP_422_UNPROCESSABLE_ENTITY
            }, status.HTTP_422_UNPROCESSABLE_ENTITY)

        authors_uuids_to_find = list()
        for author_url in authors_to_find:
            try:
                author_url_uuid = Author.get_id_from_uri(author_url)
                authors_uuids_to_find.append(author_url_uuid)
            except Exception as e:
                logging.error(e)
                logging.error("Could not parse the UUID of the given author URL for %s!" % author_url)
                continue

        friendships = Author.friends.through.objects.filter(
            from_author_id=pk,
            to_author_id__in=authors_uuids_to_find
        )
        friends = Author.objects.filter(id__in=[friendship.to_author_id for friendship in friendships])

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
                "friends": true,
                "authors":[
                    "http://127.0.0.1:8000/author/447c20fd-6fe2-4ea5-a9f7-2edabe2cc92c",
                    "http://127.0.0.1:8000/author/90926f84-1672-4f0f-873e-f2f720ae28f2"
                ]
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
