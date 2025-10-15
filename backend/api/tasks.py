import os
import subprocess
import logging
import tempfile

from celery import shared_task

from django.core.files.storage import default_storage
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .models import Video

logger = logging.getLogger(__name__)

def save_temp_file(video):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            temp_path = temp_file.name
            logger.info(f"Начало обработки видео {temp_path}")
            with default_storage.open(video.original_file.name, 'rb') as original:
                for chunk in original.chunks():
                    temp_file.write(chunk)
            return temp_path
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        raise

# How it work?
'''
Transcode to hls 
Input: key -> ; iv ->
'''

@shared_task
def transcode_to_hls(path, key, iv):
    video = Video.objects.get(id=path)
 
    temp_path = save_temp_file(video)
    # 2. Транскодируем в HLS
    output_dir = os.path.join("tmp", f"hls/{video.id}/")
    os.makedirs(output_dir, exist_ok=True)
    output_path = f"{output_dir}playlist.m3u8"
    
    logger.info(f"HLS загружен в: {output_dir}")

    cmd = f""" ffmpeg -i {temp_path} -c:v libx264 -crf 23 -preset fast -c:a aac -b:a 128k -f hls -hls_time 10 -hls_key_info_file <(echo 'http://127.0.0.1:8000/api/videos/key/{video.id}") -hls_playlist_type vod {output_path}"""
    subprocess.run(cmd, shell=True, check=True, capture_output=True,
    text=True)

    # 3. Загружаем HLS обратно в облако CDN
    django_output_path = f"hls/{video.id}/"
    for filename in os.listdir(output_dir):
        with open(f"{output_dir}{filename}", 'rb') as f:
            default_storage.save(f"{django_output_path}{filename}", f)

    # 4. Обновляем модель
    video.hls_path = f"{django_output_path}/playlist.m3u8"
    video.save()
    logger.info(f'''Полный URL: {default_storage.url(f'media/{output_dir}playlist.m3u8 {video.hls_path}')} ''')
  


@receiver(post_save, sender=Video)
def start_transcoding(sender, instance, created, **kwargs):
    if created and instance.original_file:  # Только для новых видео
        transcode_to_hls.delay(instance.id)  # Асинхронный запуск
        instance.status = 'processing'
        instance.save()