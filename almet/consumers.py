# almet/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message, Appeals
from django.utils import timezone

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.appeal_id = self.scope['url_route']['kwargs']['appeal_id']
        self.room_group_name = f'chat_{self.appeal_id}'

        # Подключаемся к группе WebSocket
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Отключаемся от группы WebSocket
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Обрабатываем полученное сообщение
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Сохраняем сообщение в базу данных
        appeal = Appeals.objects.get(id=self.appeal_id)
        message_instance = Message.objects.create(
            id_appeals=appeal,
            message=message,
            created_at=timezone.now()
        )

        # Отправляем сообщение в группу WebSocket
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_instance.message,
                'sender': f'{message_instance.id_sitizen.surname} {message_instance.id_sitizen.name}',
            }
        )

    async def chat_message(self, event):
        # Отправляем сообщение в WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
        }))
