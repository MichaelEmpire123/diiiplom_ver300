import json
import base64
import pytz
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
            edit_message_id = data.get('edit_message_id')

            if not message and 'image' not in data:
                return  # Не отправляем пустые сообщения

            # Формируем имя отправителя на основе данных пользователя
            sender_name = await self.get_sender_name(sender)
            if not sender_name:
                sender_name = "Неизвестный пользователь"  # Запасное значение

            # Если это редактирование сообщения
            if edit_message_id:
                chat_message = await self.edit_message(edit_message_id, message, sender)
                is_edited = True
            else:
                # Сохраняем новое сообщение в базе данных
                appeal = await database_sync_to_async(Appeals.objects.get)(id=self.appeal_id)
                chat_message = await self.save_message(appeal, sender, message)
                is_edited = False

            # Если есть изображение, сохраняем его
            if 'image' in data:
                await self.save_image(chat_message, data['image'])

            moscow_tz = pytz.timezone('Europe/Moscow')
            local_created_at = chat_message.created_at.astimezone(moscow_tz).strftime("%d/%m/%Y %H:%M")

            # Формируем данные для отправки
            message_data = {
                'sender_id': sender.id,
                'sender_name': sender_name,  # Убедитесь, что это поле передается
                'message': message,
                'image_url': chat_message.image.url if chat_message.image else None,
                'created_at': local_created_at,
                'message_id': chat_message.id,
                'is_edited': is_edited,
                'is_deleted': chat_message.is_deleted
            }
            print("Sending message data:", message_data)  # Логируем данные перед отправкой

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

    @database_sync_to_async
    def edit_message(self, message_id, new_message, sender):
        """Редактируем сообщение в базе данных"""
        message = Message.objects.get(id=message_id, sender=sender)
        message.message = new_message
        if not message.is_edited:  # Устанавливаем флаг is_edited только один раз
            message.is_edited = True
        message.save()
        return message

    async def chat_message(self, event):
        # Получаем сообщение из события и отправляем его пользователю
        message_data = json.loads(event['message'])
        await self.send(text_data=json.dumps(message_data))  # Отправляем все данные

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