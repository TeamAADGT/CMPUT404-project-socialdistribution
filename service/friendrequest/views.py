from rest_framework import status, viewsets
from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from service.authentication.node_basic import NodeBasicAuthentication
from service.friendrequest.serializers import FriendRequestSerializer
from social.app.models.author import Author


class FriendRequestViewSet(viewsets.ViewSet):
    serializer_class = FriendRequestSerializer
    authentication_classes = (NodeBasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    @detail_route(methods=["POST"])
    def friendrequest(self, request):
        """
        Example
            
            {
                "query":"friendrequest",
                "author": {
                    "id":"http://127.0.0.1:8000/author/4025b419-5a3c-4538-9220-d55a2c0cad7e",
                    "host":"http://127.0.0.1:8000/",
                    "displayName":"Nice Raccoon",
                    "url":"http://127.0.0.1:8000/author/4025b419-5a3c-4538-9220-d55a2c0cad7e",
                },
                "friend": {
                    "id":"http://127.0.0.1:8000/author/bd81ae42-98b5-46f6-b87f-b60cf3a39734",
                    "host":"http://127.0.0.1:8000/",
                    "displayName":"Exceptional Meow",
                    "url":"http://127.0.0.1:8000/author/4025b419-5a3c-4538-9220-d55a2c0cad7e",
                }
            }
        """

        remote_node = request.user

        serializer = FriendRequestSerializer(data=request.data)

        if serializer.is_valid():
            friend_request = serializer.save()

            # Another node is sending this on behalf of one of their local authors,
            # so this is a remote author
            remote_author_id = Author.get_id_from_uri(friend_request.author.id)

            # The target of the request is local
            friend_id = Author.get_id_from_uri(friend_request.friend.id)

            try:
                remote_author = Author.objects.get(id=remote_author_id)
            except Author.DoesNotExist:
                remote_author = remote_node.create_or_update_remote_author(remote_author_id)

            try:
                friend = Author.objects.get(id=friend_id)
            except Author.DoesNotExist:
                return Response({"detail": "No such friend exists."}, status=status.HTTP_403_FORBIDDEN)

            if not friend.activated:
                return Response(
                    {"detail": "You can't friend request an unactivated Author."},
                    status=status.HTTP_403_FORBIDDEN)

            if friend.friends_with(remote_author):
                # These two authors are already friends, so this doesn't make sense...
                return Response({"detail": "These two Authors are already friends."}, status=status.HTTP_403_FORBIDDEN)

            if friend.has_outgoing_friend_request_for(remote_author):
                # This is a friend confirmation request
                friend.accept_friend_request(remote_author)
            elif not friend.has_incoming_friend_request_from(remote_author):
                # if the target already has a friend request pending, this is redundant
                remote_author.add_friend_request(friend)

            remote_author.save()
            friend.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
