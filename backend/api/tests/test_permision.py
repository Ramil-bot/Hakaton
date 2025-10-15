from django.urls import reverse
from rest_framework.test import APITestCase
from api.models import Video, Channel
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class PermissionTests(APITestCase):
    def setUp(self):
        # Создаем трех пользователей
        self.owner = User.objects.create_user(
            email='owner@example.com',
            password='ownerpass123',
            username='videoowner'
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123',
            username='otheruser'
        )
        self.admin = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            username='admin'
        )
        
        # Создаем канал и видео
        self.channel = Channel.objects.create(
            name='Permission Test Channel',
            owner=self.owner
        )
        self.video = Video.objects.create(
            title='Permission Test Video',
            owner=self.channel,
            original_file='videos/permission_test.mp4',
            status='processed'
        ) 
        
        # Получаем токены
        self.owner_token = str(RefreshToken.for_user(self.owner).access_token)
        self.other_token = str(RefreshToken.for_user(self.other_user).access_token)
        self.admin_token = str(RefreshToken.for_user(self.admin).access_token)

    def test_owner_can_edit_video(self):
        """Тест что владелец может редактировать видео"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        url = reverse('video-detail', args=[self.video.id])
        data = {'title': 'Updated Title'}
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.video.refresh_from_db()
        self.assertEqual(self.video.title, 'Updated Title')

    def test_non_owner_cannot_edit_video(self):
        """Тест что другие пользователи не могут редактировать видео"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.other_token}')
        url = reverse('video-detail', args=[self.video.id])
        data = {'title': 'Hacked Title'}
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_any_video(self):
        """Тест что админ может удалять любые видео"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        url = reverse('video-detail', args=[self.video.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Video.objects.count(), 0)

    def test_age_restricted_access(self):
        """Тест доступа к возрастному контенту"""
        # Помечаем видео как 18+
        self.video.age_restricted = True
        self.video.save()
        
        # Попытка доступа без подтверждения возраста
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.other_token}')
        url = reverse('video-detail', args=[self.video.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)