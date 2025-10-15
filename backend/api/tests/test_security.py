from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from api.models import Video, Channel
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

User = get_user_model()

class SecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            email='security@example.com',
            password='securepass123',
            username='securityuser'
        )
        self.channel = Channel.objects.create(
            name='Security Channel',
            owner=self.owner
        )
        self.video = Video.objects.create(
            title='Security Test Video',
            channel=self.channel,
            file='videos/security_test.mp4',
            status='processed'
        )

    def test_jwt_token_required_for_upload(self):
        """Тест что загрузка видео требует JWT токена"""
        url = reverse('video-upload')
        with open('test_files/sample.mp4', 'rb') as video_file:
            data = {'title': 'No Token Video', 'file': video_file}
            response = self.client.post(url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_anti_malware_scan(self):
        """Тест сканирования загружаемых файлов (мок)"""
        from api.utils import scan_for_malware
        # Тест с безопасным файлом
        safe_file = 'test_files/sample.mp4'
        self.assertFalse(scan_for_malware(safe_file))
        
        # Тест с "опасным" файлом (мок)
        dangerous_file = 'test_files/malicious.exe'
        self.assertTrue(scan_for_malware(dangerous_file))

    def test_private_video_access_control(self):
        """Тест контроля доступа к приватным видео"""
        private_video = Video.objects.create(
            title='Private Video',
            channel=self.channel,
            file='videos/private.mp4',
            status='processed',
            visibility='private'
        )
        
        # Попытка доступа без авторизации
        url = reverse('video-detail', args=[private_video.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Попытка доступа другого пользователя
        other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123'
        )
        refresh = RefreshToken.for_user(other_user)
        token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)