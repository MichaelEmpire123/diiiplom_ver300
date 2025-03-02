import json
import base64
import pytz
import re
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Appeals, Message, ChatCommand, CannedResponse
from django.core.files.base import ContentFile

BAD_WORDS = ["попа", "пипец"]  # Список запрещённых слов

def censor_message(message):
    pattern = re.compile(r'\b(' + '|'.join(BAD_WORDS) + r')\b', re.IGNORECASE)
    return pattern.sub("***", message)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.appeal_id = self.scope['url_route']['kwargs']['appeal_id']
        self.user = self.scope.get('user', None)

        if self.user and self.user.is_authenticated:
            self.chat_group_name = f'chat_{self.appeal_id}'
            await self.channel_layer.group_add(self.chat_group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.chat_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data.get('message')
            sender = self.user
            edit_message_id = data.get('edit_message_id')

            if not message and 'image' not in data:
                return

            # Проверка, является ли сообщение командой
            if message.startswith("/"):
                if await self.is_service_employee(sender):
                    response = await self.get_canned_response(message)
                    if response:
                        await self.send(text_data=json.dumps({"message": response, "sender": "Система"}))
                        return
                else:
                    await self.send(text_data=json.dumps({"message": "У вас нет прав на выполнение команд.", "sender": "Система"}))
                    return

            sender_name = await self.get_sender_name(sender)
            sender_name = sender_name if sender_name else "Неизвестный пользователь"

            if edit_message_id:
                chat_message = await self.edit_message(edit_message_id, message, sender)
                is_edited = True
            else:
                appeal = await database_sync_to_async(Appeals.objects.get)(id=self.appeal_id)
                message = await database_sync_to_async(censor_message)(message)
                chat_message = await self.save_message(appeal, sender, message)
                is_edited = False

            if 'image' in data:
                await self.save_image(chat_message, data['image'])

            moscow_tz = pytz.timezone('Europe/Moscow')
            local_created_at = chat_message.created_at.astimezone(moscow_tz).strftime("%d/%m/%Y %H:%M")

            message_data = {
                'sender_id': sender.id,
                'sender_name': sender_name,
                'message': message,
                'image_url': chat_message.image.url if chat_message.image else None,
                'created_at': local_created_at,
                'message_id': chat_message.id,
                'is_edited': is_edited,
                'is_deleted': chat_message.is_deleted
            }

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
    def is_service_employee(self, user):
        """Проверяет, является ли пользователь сотрудником службы."""
        return user.id_sotrudnik is not None

    @database_sync_to_async
    def edit_message(self, message_id, new_message, sender):
        message = Message.objects.get(id=message_id, sender=sender)
        message.message = censor_message(new_message)
        if not message.is_edited:
            message.is_edited = True
        message.save()
        return message

    async def chat_message(self, event):
        message_data = json.loads(event['message'])
        await self.send(text_data=json.dumps(message_data))

    @database_sync_to_async
    def get_sender_name(self, sender):
        if sender.id_citizen:
            return f"{sender.id_citizen.surname} {sender.id_citizen.name}"
        elif sender.id_sotrudnik:
            return f"{sender.id_sotrudnik.id_service.name}"
        else:
            return "Админ"

    @database_sync_to_async
    def save_message(self, appeal, sender, message):
        return Message.objects.create(
            id_appeals=appeal,
            sender=sender,
            message=message
        )

    @database_sync_to_async
    def save_image(self, chat_message, image_data):
        image_format, image_str = image_data.split(';base64,')
        ext = image_format.split('/')[-1]
        image_file = base64.b64decode(image_str)
        chat_message.image.save(f"message_{chat_message.id}.{ext}", ContentFile(image_file), save=True)

    @database_sync_to_async
    def get_canned_response(self, command):
        """Получает готовый ответ на команду."""
        try:
            cmd = ChatCommand.objects.get(command=command)
            response = CannedResponse.objects.filter(command=cmd).first()
            return response.response_text if response else "Нет готовых ответов."
        except ChatCommand.DoesNotExist:
            return None
