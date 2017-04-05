from rest_framework import viewsets, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse

from service.authentication.node_basic import NodeBasicAuthentication
from service.authors.serializers import AuthorSerializer, AuthorURLSerializer
from social.app.models.author import Author


class AuthorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = (IsAuthenticated,)

    @detail_route(methods=["GET"], authentication_classes=(NodeBasicAuthentication,))
    def author_friends(self, request, pk=None):
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

    @detail_route(methods=["POST"], authentication_classes=(SessionAuthentication,))
    def follow(self, request, pk=None):

        follower = request.user.profile

        if not follower.activated:
            return Response(
                {"detail": "Unactivated authors cannot follow other authors."},
                status=status.HTTP_403_FORBIDDEN)

        try:
            followee = Author.objects.get(id=pk)
        except Author.DoesNotExist:
            return Response(
                {'detail': 'The author you wanted to follow could not be found.'},
                status=status.HTTP_404_NOT_FOUND)

        # Does this author already follow followee?
        if follower.followed_authors.filter(id=followee.id):
            return Response(
                {"detail": "You already follow this author."},
                status=status.HTTP_403_FORBIDDEN)

        if not followee.activated:
            return Response(
                {"detail": "Unactivated authors cannot be followed."},
                status=status.HTTP_403_FORBIDDEN)

        follower.followed_authors.add(followee)

        return Response(
            {"followed_author": reverse("service:author-detail", kwargs={'pk': followee.id}, request=request)},
            status=status.HTTP_200_OK)

    @detail_route(methods=["POST"], authentication_classes=(SessionAuthentication,))
    def unfollow(self, request, pk=None):

        unfollower = request.user.profile

        if not unfollower.activated:
            return Response(
                {"detail": "Unactivated authors cannot unfollow other authors."},
                status=status.HTTP_403_FORBIDDEN)

        try:
            followee = Author.objects.get(id=pk)
        except Author.DoesNotExist:
            return Response(
                {'detail': 'The author you wanted to unfollow could not be found.'},
                status=status.HTTP_404_NOT_FOUND)

        if not followee.activated:
            return Response(
                {"detail": "Unactivated authors cannot be unfollowed."},
                status=status.HTTP_403_FORBIDDEN)

        # Does this author already not follow followee?
        if not unfollower.followed_authors.filter(id=followee.id):
            return Response(
                {"detail": "You already do not follow this author."},
                status=status.HTTP_403_FORBIDDEN)

        unfollower.followed_authors.remove(followee)

        return Response(
            {"unfollowed_author": reverse("service:author-detail", kwargs={'pk': followee.id}, request=request)},
            status=status.HTTP_200_OK)

    @detail_route(methods=["POST"], authentication_classes=(SessionAuthentication,))
    def friendrequest(self, request, pk=None):

        current_author = request.user.profile

        if not current_author.activated:
            return Response(
                {"detail": "Unactivated authors cannot friend request other authors."},
                status=status.HTTP_403_FORBIDDEN)

        try:
            target = Author.objects.get(id=pk)
        except Author.DoesNotExist:
            return Response(
                {'detail': 'The author you wanted to friend request could not be found.'},
                status=status.HTTP_404_NOT_FOUND)

        if current_author.friends.filter(id=target.id):
            return Response(
                {"detail": "You are already friends with this author."},
                status=status.HTTP_403_FORBIDDEN)

        if current_author.outgoing_friend_requests.filter(id=target.id):
            return Response(
                {"detail": "You already have a pending friend request with this author."},
                status=status.HTTP_403_FORBIDDEN)

        if not target.activated:
            return Response(
                {"detail": "Unactivated authors cannot be friend requested."},
                status=status.HTTP_403_FORBIDDEN)

        current_author.add_friend_request(target)

        return Response(
            {"friend_requested_author": reverse("service:author-detail", kwargs={'pk': target.id}, request=request)},
            status=status.HTTP_200_OK)

    def two_authors_are_friends(request, local_id=None, other_host_name=None, other_id=None):
        """
        Returns true if these two authors are found, and 
        """
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)
