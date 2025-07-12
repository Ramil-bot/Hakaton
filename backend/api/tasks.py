from celery import shared_task
import subprocess
from django.core.files.storage import default_storage
from .models import Video
from django.dispatch import receiver
from django.db.models.signals import post_save
import logging


logger = logging.getLogger(__name__)


@shared_task
def transcode_to_hls(video_id):
    video = Video.objects.get(id=video_id)
    logger.info(f"Начало обработки видео {video_id}")
    
    # 1. Скачиваем оригинал из облака во временный файл
    with default_storage.open(video.original_file.name) as original:
        temp_path = f"/tmp/{video.original_file.name}"
        with open(temp_path, 'wb') as f:
            f.write(original.read())
    
    logger.info(f"HLS загружен в: media/{output_dir}")

    # 2. Транскодируем в HLS
    output_dir = f"hls/{video.id}/"
    output_path = f"{output_dir}playlist.m3u8"
    
    cmd = f"""
    ffmpeg -i {temp_path} \
    -c:v libx264 -crf 23 -preset fast \
    -c:a aac -b:a 128k \
    -f hls -hls_time 10 -hls_playlist_type vod \
    {output_path}
    """
    subprocess.run(cmd, shell=True, check=True, capture_output=True,
    text=True)
    
    # 3. Загружаем HLS обратно в облако
    for filename in os.listdir(output_dir):
        with open(f"{output_dir}{filename}", 'rb') as f:
            default_storage.save(f"media/{output_dir}{filename}", f)
    
    # 4. Обновляем модель
    video.hls_path = f"media/{output_dir}playlist.m3u8"
    video.save()
    logger.info(f"Полный URL: {default_storage.url(f'media/{output_dir}playlist.m3u8')}")
  


@receiver(post_save, sender=Video)
def start_transcoding(sender, instance, created, **kwargs):
    if created and instance.original_file:  # Только для новых видео
        transcode_to_hls.delay(instance.id)  # Асинхронный запуск
        instance.status = 'processing'
        instance.save()