from rest_framework import status, viewsets
from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.serializers import Serializer

from service.authentication.session import AuthorSessionAuthentication
from social.app.models.author import Author


class InternalAPIViewSet(viewsets.GenericViewSet):
    authentication_classes = (AuthorSessionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = Serializer

    @detail_route(["POST"])
    def follow(self, request, pk=None):
        """
        Internal endpoint used by the website's Author detail page to allow the currently logged in Author to follow another
        Author.
        
        For local AJAX use only.

        ### Parameters
        * id: The ID of the author to be followed. (UUID, required)
        
        ### Example Successful Response

            { 
                "followed_author": "http://site/service/author/62309fbb-72c5-4dce-bf65-4a3bf9b92f09"
            }
            
        Used on `/social/app/templates/app/author_detail.html'.
        """
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

    @detail_route(["POST"])
    def unfollow(self, request, pk=None):
        """
        Internal endpoint used by the website's Author detail page to allow the currently logged in Author to unfollow another
        Author.
        
        For local AJAX use only.
        
        ### Parameters
        * id: The ID of the author to be unfollowed. (UUID, required)
        
        ### Example Successful Response

            { 
                "unfollowed_author": "http://site/service/author/62309fbb-72c5-4dce-bf65-4a3bf9b92f09"
            }
            
        Used on `/social/app/templates/app/author_detail.html'.
        """
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

    @detail_route(["POST"])
    def friendrequest(self, request, pk=None):
        """
        Internal endpoint used by the website's Author detail page to allow the currently logged in Author to send a 
        friend request to another Author.
        
        If the target author is remote, it sends a request to the remote Node's `/friendrequest/` endpoint.
        
        For local AJAX use only.
        
        ### Parameters
        * id: The ID of the author to be sent a friend request. (UUID, required)
        
        ### Example Successful Response

            { 
                "friend_requested_author": "http://site/service/author/62309fbb-72c5-4dce-bf65-4a3bf9b92f09"
            }
            
        Used on `/social/app/templates/app/author_detail.html'.
        """
        current_author = request.user.profile

        if not current_author.activated:
            return Response(
                {"detail": "Unactivated authors cannot friend request other authors."},
                status=status.HTTP_403_FORBIDDEN)

        try:
            # This is triggered by an AJAX call on our website, on an Author's page,
            # so it's not possible for it to not be in our database unless something unintended is happening
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

        if target.node.local:
            current_author.add_friend_request(target)
        else:
            r = target.node.post_friend_request(request, current_author, target)

            if 200 <= r.status_code < 300:
                # Success!
                current_author.add_friend_request(target)
            else:
                return Response(
                    {"detail": "Remote friend request failed."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(
            {"friend_requested_author": reverse("service:author-detail", kwargs={'pk': target.id},
                                                request=request)},
            status=status.HTTP_200_OK)
