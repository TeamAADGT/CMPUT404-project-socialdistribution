from rest_framework import permissions
from rest_framework import viewsets

from service.nodes.serializers import NodeSerializer
from social.app.models.node import Node


class NodeViewSet(viewsets.ModelViewSet):
    queryset = Node.objects.all()
    serializer_class = NodeSerializer
    permission_classes = (permissions.IsAdminUser,)
