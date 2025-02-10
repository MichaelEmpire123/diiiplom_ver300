import json
import base64
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Appeals, Message
from django.core.files.base import ContentFile

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.appeal_id = self.scope['url_route']['kwargs']['appeal_id']
        self.user = self.scope.get('user', None)

        # Проверяем, авторизован ли пользователь
        if self.user and self.user.is_authenticated:
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
        try:
            data = json.loads(text_data)
            message = data.get('message')
            sender = self.user

            if not message and 'image' not in data:
                return  # Не отправляем пустые сообщения

            # Формируем имя отправителя на основе данных пользователя
            sender_name = await self.get_sender_name(sender)

            # Сохраняем сообщение в базе данных
            appeal = await database_sync_to_async(Appeals.objects.get)(id=self.appeal_id)
            chat_message = await self.save_message(appeal, sender, message)

            # Если есть изображение, сохраняем его
            if 'image' in data:
                await self.save_image(chat_message, data['image'])

            # Формируем данные для отправки
            message_data = {
                'sender_id': sender.id,
                'sender_name': sender_name,  # Используем корректное имя
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
        except Appeals.DoesNotExist:
            await self.send(text_data=json.dumps({'error': 'Appeal not found'}))
        except Exception as e:
            await self.send(text_data=json.dumps({'error': str(e)}))

    async def chat_message(self, event):
        # Получаем сообщение из события и отправляем его пользователю
        message = event['message']
        await self.send(text_data=message)

    @database_sync_to_async
    def get_sender_name(self, sender):
        """Формируем имя отправителя на основе данных пользователя"""
        if sender.id_citizen:
            return f"{sender.id_citizen.surname} {sender.id_citizen.name}"
        elif sender.id_sotrudnik:
            return f"{sender.id_sotrudnik.id_service.name}"
        else:
            return "Админ"

    @database_sync_to_async
    def save_message(self, appeal, sender, message):
        """Сохраняем сообщение в базе данных"""
        return Message.objects.create(
            id_appeals=appeal,
            sender=sender,
            message=message
        )

    @database_sync_to_async
    def save_image(self, chat_message, image_data):
        """Сохраняем изображение в базе данных"""
        image_format, image_str = image_data.split(';base64,')
        ext = image_format.split('/')[-1]
        image_file = base64.b64decode(image_str)
        chat_message.image.save(f"message_{chat_message.id}.{ext}", ContentFile(image_file), save=True)