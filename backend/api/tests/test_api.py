from django.test import TestCase
from django.core.exceptions import ValidationError
from api.models import Video, Channel, Comment
from django.contrib.auth import get_user_model
import os

User = get_user_model()

class VideoModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email='creator@example.com',
            password='testpass123',
            username='videocreator'
        )
        self.channel = Channel.objects.create(
            name='Test Channel',
            owner=self.owner
        )

    def test_create_video(self):
        """Тест создания видео с валидными данными"""
        video = Video.objects.create(
            title='Test Video',
            owner=self.channel,
            original_file='videos/test.mp4',
            duration=120,
            status='processed'
        )
        self.assertEqual(video.title, 'Test Video')
        self.assertEqual(video.views_count, 0)  # Default value
        # self.assertTrue(video.upload_date is not None)

    def test_video_str_representation(self):
        """Тест строкового представления видео"""
        video = Video.objects.create(
            title='Test Video',
            owner=self.channel,
            original_file='videos/test.mp4'
        )
        self.assertEqual(str(video), 'Test Video')

    # def test_invalid_video_status(self):
    #     """Тест невалидного статуса видео"""
    #     with self.assertRaises(ValidationError):
    #         video = Video(
    #             title='Invalid Status Video',
    #             channel=self.channel,
    #             file='videos/test.mp4',
    #             status='invalid_status'
    #         )
    #         video.full_clean()

    # def test_video_thumbnails_generation(self):
    #     """Тест генерации превью для видео (мок)"""
    #     video = Video.objects.create(
    #         title='Thumbnail Test',
    #         channel=self.channel,
    #         file='videos/thumbnail_test.mp4'
    #     )
    #     video.generate_thumbnails()
    #     self.assertTrue(video.thumbnail.name.startswith('thumbnails/'))