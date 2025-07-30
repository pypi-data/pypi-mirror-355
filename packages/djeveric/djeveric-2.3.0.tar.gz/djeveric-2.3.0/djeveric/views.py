from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from djeveric.models import ConfirmableModelMixin
from djeveric.serializers import ConfirmationSerializer


class ConfirmModelMixin:
    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_confirm(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_confirm(self, instance: ConfirmableModelMixin):
        instance.confirm()

    def get_confirm_queryset(self):
        if hasattr(self, "confirm_queryset"):
            return self.confirm_queryset
        return super().get_queryset()

    def get_basic_queryset(self):
        """
        :return: The queryset for the basic Rest Framework actions (create, retrieve, update, delete and list)
        """
        return super().get_queryset()

    def get_permissions(self):
        if self.action == "confirm":
            return [AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        if self.action == "confirm":
            return self.get_confirm_queryset()
        return self.get_basic_queryset()

    def get_serializer_class(self):
        if self.action == "confirm":
            return ConfirmationSerializer
        return super().get_serializer_class()
