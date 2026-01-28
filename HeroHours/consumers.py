import json

from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.decorators import permission_required
from djangochannelsrestframework.decorators import action
from djangochannelsrestframework.observer import model_observer
from djangochannelsrestframework.observer.generics import ObserverModelInstanceMixin
from djangochannelsrestframework.permissions import WrappedDRFPermission, IsAuthenticated
from rest_framework import serializers
from rest_framework.permissions import DjangoModelPermissions

from . import models
from djangochannelsrestframework import permissions
from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework.mixins import (
    ListModelMixin, RetrieveModelMixin,
)
from django.db.models.expressions import BaseExpression

from .models import Users


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['User_ID', 'First_Name', 'Last_Name', 'Checked_In', 'Total_Seconds', 'Last_In', 'Last_Out']
class LiveConsumer(ObserverModelInstanceMixin, RetrieveModelMixin, ListModelMixin, GenericAsyncAPIConsumer):
    queryset = Users.objects.all().order_by('Last_Name','First_Name')
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated]

    @model_observer(Users)
    async def update_activity(
            self,
            message: MemberSerializer,
            observer=None,
            subscribing_request_ids=[],
            **kwargs
    ):
        await self.send_json({'data':message.data, 'request_ids':subscribing_request_ids})

    @update_activity.serializer
    def update_activity(self, instance: Users, action, **kwargs) -> MemberSerializer:
        """This will return the comment serializer"""
        for field in instance._meta.fields:
            if isinstance(getattr(instance, field.name), BaseExpression):
                instance.refresh_from_db()
                break
        return MemberSerializer(instance)

    @action()
    async def subscribe_all(self, request_id, **kwargs):
        await self.update_activity.subscribe(request_id=request_id)