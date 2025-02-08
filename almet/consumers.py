import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message, Appeals
from django.utils import timezone
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.appeal_id = self.scope['url_route']['kwargs']['appeal_id']
        self.room_group_name = f'chat_{self.appeal_id}'
        user = self.scope['user']

        # Получаем жалобу асинхронно
        appeal = await self.get_appeal(self.appeal_id)

        # Логируем только после того, как все данные будут получены
        user_id_citizen = await self.get_user_id_citizen(user)
        appeal_id_sitizen = appeal.id_sitizen
        appeal_id_service = appeal.id_service
        user_id_service = await self.get_user_id_service(user)

        logger.info(f"Checking access for user {user.email}:")
        logger.info(f"User ID Citizen: {user_id_citizen}, Appeal ID Citizen: {appeal_id_sitizen}")
        logger.info(f"User ID Service: {user_id_service}, Appeal ID Service: {appeal_id_service}")

        # Проверяем, является ли пользователь:
        # - Жителем, который создал обращение, или
        # - Сотрудником службы, на которую направлено обращение
        if user_id_citizen == appeal_id_sitizen or user_id_service == appeal_id_service:
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
        else:
            logger.warning(f"ACCESS DENIED: User {user.email} tried to access chat {self.appeal_id}")
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        image = data.get('image', None)

        # Получаем жалобу асинхронно
        appeal = await self.get_appeal(self.appeal_id)
        user = self.scope['user']

        # Создаем сообщение
        message_instance = await self.create_message(appeal, user, message, image)

        # Отправляем сообщение в группу
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_instance.message,
                'sender': message_instance.sender.email,
                'image_url': message_instance.image.url if message_instance.image else None,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'image_url': event['image_url'],
        }))

    @sync_to_async
    def get_appeal(self, appeal_id):
        # Используем select_related для связанной модели, чтобы избежать дополнительных запросов
        return Appeals.objects.select_related('id_sitizen', 'id_service').get(id=appeal_id)

    @sync_to_async
    def create_message(self, appeal, sender, message, image):
        return Message.objects.create(
            id_appeals=appeal,
            sender=sender,
            message=message,
            image=image,
            created_at=timezone.now()
        )

    @sync_to_async
    def get_user_id_citizen(self, user):
        return user.id_citizen if hasattr(user, 'id_citizen') else None

    @sync_to_async
    def get_user_id_service(self, user):
        if hasattr(user, 'id_sotrudnik') and user.id_sotrudnik is not None:
            return user.id_sotrudnik.id_service
        return None

