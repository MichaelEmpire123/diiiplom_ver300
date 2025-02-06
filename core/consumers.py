import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.shortcuts import get_object_or_404
from .models import Message, Appeals
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.appeal_id = self.scope['url_route']['kwargs']['appeal_id']
        self.appeal = get_object_or_404(Appeals, id=self.appeal_id)

        # Создание уникальной комнаты для чата
        self.room_name = f'chat_{self.appeal_id}'
        self.room_group_name = f'chat_{self.appeal_id}'

        # Присоединение к комнате WebSocket
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Разрешение подключения
        await self.accept()

    async def disconnect(self, close_code):
        # Отключение от комнаты
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Получение сообщения от WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        image = text_data_json.get('image', None)

        user = self.scope['user']

        # Создание нового сообщения
        new_message = Message.objects.create(
            id_appeals=self.appeal,
            message=message,
            image=image if image else None,
            created_at=timezone.now(),
            id_sotrudnik=user.id_sotrudnik if user.id_sotrudnik else None,
            id_sitizen=user.id_citizen if user.id_citizen else None,
        )

        # Отправка сообщения всем клиентам в группе
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message_html': new_message.message,
                'user': f"{new_message.id_sotrudnik.name if new_message.id_sotrudnik else new_message.id_sitizen.name}",
                'image_url': new_message.image.url if new_message.image else None
            }
        )

    # Отправка сообщения клиентам
    async def chat_message(self, event):
        message_html = event['message_html']
        user = event['user']
        image_url = event['image_url']

        # Отправка сообщения на WebSocket
        await self.send(text_data=json.dumps({
            'message_html': message_html,
            'user': user,
            'image_url': image_url
        }))
