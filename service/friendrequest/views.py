from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from service.authentication.node_basic import NodeBasicAuthentication
from service.friendrequest.serializers import FriendRequestSerializer
from social.app.models.author import Author


@api_view(["POST"])
@authentication_classes((NodeBasicAuthentication,))
@permission_classes((IsAuthenticated,))
def friendrequest(request):
    """
    Example </br>
    <pre>
    {
        &nbsp&nbsp&nbsp"query":"friendrequest",
        &nbsp&nbsp&nbsp"author": {
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"id":"http://127.0.0.1:8000/author/4025b419-5a3c-4538-9220-d55a2c0cad7e",
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"host":"http://127.0.0.1:8000/",
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"displayName":"Nice Raccoon",
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"url":"http://127.0.0.1:8000/author/4025b419-5a3c-4538-9220-d55a2c0cad7e",
        &nbsp&nbsp&nbsp},
        &nbsp&nbsp&nbsp"friend": {
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"id":"http://127.0.0.1:8000/author/bd81ae42-98b5-46f6-b87f-b60cf3a39734",
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"host":"http://127.0.0.1:8000/",
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"displayName":"Exceptional Meow",
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"url":"http://127.0.0.1:8000/author/4025b419-5a3c-4538-9220-d55a2c0cad7e",
        &nbsp&nbsp&nbsp}
    }
    </pre>
    """
    # Needs to be revamped to support remote authors
    # Return 501 Not Implemented
    return Response(status=501)

    # serializer = FriendRequestSerializer(data=request.data)
    #
    # if serializer.is_valid():
    #     friend_request = serializer.save()
    #
    #     # TODO: Add code to handle case when one or more users are remote
    #     author_id = friend_request.author.get_id_without_url()
    #     friend_id = friend_request.friend.get_id_without_url()
    #
    #     author = Author.objects.get(id=author_id)
    #
    #     # TODO: Allow for case where remote server submitted this on behalf of another user
    #     if author.user_id != request.user.id:
    #         return Response(status=status.HTTP_403_FORBIDDEN)
    #
    #     friend = Author.objects.get(id=friend_id)
    #
    #     author.add_friend_request(friend)
    #     author.save()
    #     return Response(serializer.data, status=status.HTTP_200_OK)
    #
    # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
