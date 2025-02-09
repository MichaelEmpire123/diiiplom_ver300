# consumers.py
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Appeals, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.appeal_id = self.scope['url_route']['kwargs']['appeal_id']
        self.user = self.scope.get('user', None)

        # Проверяем, авторизован ли пользователь
        if self.user.is_authenticated:
            # Подключаемся к группе по appeal_id
            self.chat_group_name = f'chat_{self.appeal_id}'
            await self.channel_layer.group_add(
                self.chat_group_name,
                self.channel_name
            )

            await self.accept()
        else:
            # Если пользователь не авторизован, отклоняем соединение
            await self.close()

    async def disconnect(self, close_code):
        # Отключаемся от группы
        await self.channel_layer.group_discard(
            self.chat_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Получаем сообщение
        data = json.loads(text_data)
        message = data['message']
        sender_name = data.get('sender_name', 'Неизвестный пользователь')

        # Сохраняем сообщение в базе данных
        appeal = await database_sync_to_async(Appeals.objects.get)(id=self.appeal_id)
        sender = self.user
        chat_message = await database_sync_to_async(Message.objects.create)(
            id_appeals=appeal,
            sender=sender,
            message=message
        )

        # Отправляем сообщение всем подключенным пользователям
        message_data = {
            'sender_id': sender.id,
            'sender_name': sender_name,
            'message': message,
            'image_url': chat_message.image.url if chat_message.image else None
        }

        # Отправляем сообщение в группу WebSocket
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'chat_message',
                'message': json.dumps(message_data)
            }
        )

    async def chat_message(self, event):
        # Получаем сообщение из события и отправляем его пользователю
        message = event['message']
        await self.send(text_data=message)
