from django.test import TestCase
from api.models import Video, Channel
from api.tasks import transcode_to_hls #generate_thumbnails
from django.contrib.auth import get_user_model
from unittest import mock

User = get_user_model()

class VideoProcessingTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email='processor@example.com',
            password='testpass123'
        )
        self.channel = Channel.objects.create(
            name='Processing Channel',
            owner=self.owner
        )
        self.video = Video.objects.create(
            title='Raw Video',
            channel=self.channel,
            file='videos/raw.mp4',
            status='uploaded'
        )

    @mock.patch('videos.tasks.subprocess.run')
    def test_video_processing(self, mock_subprocess):
        """Тест обработки видео (транскодинг)"""
        # Настраиваем мок для успешного выполнения
        mock_subprocess.return_value.returncode = 0
        
        transcode_to_hls(self.video.id)
        
        self.video.refresh_from_db()
        self.assertEqual(self.video.status, 'processed')
        self.assertTrue(self.video.processed_file.name.startswith('processed/'))

    @mock.patch('videos.tasks.subprocess.run')
    def test_processing_failure(self, mock_subprocess):
        """Тест обработки ошибки при транскодинге"""
        # Настраиваем мок для неудачного выполнения
        mock_subprocess.return_value.returncode = 1
        
        transcode_to_hls(self.video.id)
        
        self.video.refresh_from_db()
        self.assertEqual(self.video.status, 'failed')

    # @mock.patch('videos.tasks.FFmpeg')
    # def test_thumbnail_generation(self, mock_ffmpeg):
    #     """Тест генерации превью"""
    #     # Настраиваем мок FFmpeg
    #     mock_instance = mock_ffmpeg.return_value
    #     mock_instance.input.return_value.filter.return_value.output.return_value.run.return_value = True
        
    #     generate_thumbnails(self.video.id)
        
    #     self.video.refresh_from_db()
    #     self.assertTrue(self.video.thumbnail.name.startswith('thumbnails/'))