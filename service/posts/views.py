from rest_framework import viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from service.posts.serializers import PostSerializer
from social.app.models.post import Post


class PublicPostsViewSet(viewsets.ViewSet):
    def list(self, request):
        queryset = Post.objects.filter(visibility="PUBLIC")
        serializer = PostSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Post.objects.all()
        post = get_object_or_404(queryset, pk)
        serializer = PostSerializer(post, context={'request': request})
        return Response(serializer.data)
