import os
import subprocess
import logging
import tempfile

from celery import shared_task

from django.core.files.storage import default_storage
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.files.base import ContentFile
from django.conf import settings
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .models import Video

logger = logging.getLogger(__name__)

def get_video_duration(temp_path):
    """Получает длительность видео в секундах"""
    try:
        duration_cmd = [
            'ffprobe', 
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            temp_path
        ]
        
        result = subprocess.run(duration_cmd, capture_output=True, text=True)
        duration = float(result.stdout.strip())
        logger.info(f"Длительность видео: {duration} секунд")
        return duration
    except Exception as e:
        logger.error(f"Ошибка получения длительности видео: {str(e)}")
        return 0


def generate_thumbnails(video, temp_path):
    """Генерация превью для видео"""
    try:
        # Создаем временную директорию для превью
        thumb_dir = os.path.join("tmp", f"thumbs/{video.id}/")
        os.makedirs(thumb_dir, exist_ok=True)
        
        # Получаем длительность видео
        duration_cmd = [
            'ffprobe', 
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            temp_path
        ]
        
        result = subprocess.run(duration_cmd, capture_output=True, text=True)
        duration = float(result.stdout.strip())
        
        logger.info(f"Длительность видео: {duration} секунд")
        
        # Генерируем превью в разные моменты времени
        thumb_times = [
            0,  # начало
            duration * 0.25,  # 25%
            duration * 0.5,   # 50%
            duration * 0.75,  # 75%
            duration - 1      # конец (минус 1 секунда)
        ]
        
        thumb_paths = []
        
        for i, time in enumerate(thumb_times):
            if time < 0:
                continue
                
            thumb_path = os.path.join(thumb_dir, f"thumb_{i}.jpg")
            
            cmd = [
                'ffmpeg',
                '-ss', str(time),  # временная метка
                '-i', temp_path,
                '-vframes', '1',   # один кадр
                '-q:v', '2',       # качество (2 - лучшее)
                '-vf', 'scale=320:-1',  # масштабирование до ширины 320px
                '-y',              # перезаписать если существует
                thumb_path
            ]
            
            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=30)
                if os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 0:
                    thumb_paths.append(thumb_path)
                    logger.info(f"Создано превью {i+1}/{len(thumb_times)}")
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                logger.warning(f"Не удалось создать превью в {time}с: {e}")
                continue
        
        # Выбираем лучшее превью (самое большое по размеру)
        if thumb_paths:
            best_thumb = max(thumb_paths, key=lambda x: os.path.getsize(x))
            
            # Сохраняем основное превью
            with open(best_thumb, 'rb') as f:
                video.thumbnail.save(f"thumbnail_{video.id}.jpg", ContentFile(f.read()))
            
            # Сохраняем дополнительные превью (если нужно)
            for i, thumb_path in enumerate(thumb_paths):
                if thumb_path == best_thumb:
                    continue
                    
                with open(thumb_path, 'rb') as f:
                    # Здесь можно сохранить дополнительные превью, если нужно
                    pass
            
            logger.info(f"Основное превью сохранено: {video.thumbnail.name}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Ошибка генерации превью: {str(e)}")
        return False
    
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
def transcode_to_hls(id):
    try:
        video = Video.objects.get(id=id)
        temp_path = save_temp_file(video)

        duration = get_video_duration(temp_path)
        temp_path = save_temp_file(video)
        # 2. Транскодируем в HLS
        output_dir = os.path.join("tmp", f"hls/{video.id}/")
        os.makedirs(output_dir, exist_ok=True)
        output_path = f"{output_dir}playlist.m3u8"
        
        logger.info(f"HLS загружен в: {output_dir}")
         # Генерируем превью ДО транскодирования
        logger.info("Начинаем генерацию превью...")
        thumbnail_generated = generate_thumbnails(video, temp_path)
        if thumbnail_generated:
            video.save()  # Сохраняем превью
            logger.info("Превью успешно сгенерировано")
        else:
            logger.warning("Не удалось сгенерировать превью")
        

        key_info_content = f"""http://127.0.0.1:8000/api/videos/key/{video.id}{output_dir}enc.key"""
        key_info_path = f"{output_dir}key_info.txt"
        
        with open(key_info_path, 'w') as f:
            f.write(key_info_content)
        
        # Генерируем случайный ключ шифрования
        encryption_key = os.urandom(16)  # 128 бит для AES-128
        key_file_path = f"{output_dir}enc.key"
        
        with open(key_file_path, 'wb') as f:
            f.write(encryption_key)
        
        # Сохраняем ключ в модели видео (закодированным в base64)
        import base64
        video.encryption_key = base64.b64encode(encryption_key).decode('utf-8')
        video.save()

        cmd = f""" ffmpeg -i {temp_path} -c:v libx264 -crf 23 -preset fast -c:a aac -b:a 128k -f hls -hls_time 10 {output_path}"""
        # cmd = f""" ffmpeg -i {temp_path} -c:v libx264 -crf 23 -preset fast -c:a aac -b:a 128k -f hls -hls_time 10 -hls_key_info_file {key_info_path} '-hls_segment_filename' {f'{output_dir}segment_%03d.ts'} -hls_playlist_type vod {output_path}"""
        # cmd = [
        #         'ffmpeg',
        #         '-i', temp_path,
        #         '-c:v', 'libx264',
        #         '-c:a', 'aac',
        #         '-f', 'hls',
        #         '-hls_time', '10',
        #         output_path
        #     ]
        subprocess.run(cmd, shell=True, check=True, capture_output=True,
        text=True)

        # 3. Загружаем HLS обратно в облако CDN
        django_output_path = f"hls/{video.id}/"
        for filename in os.listdir(output_dir):
            with open(f"{output_dir}{filename}", 'rb') as f:
                default_storage.save(f"{django_output_path}{filename}", f)

        # 4. Обновляем модель
        video.hls_path = f"{django_output_path}playlist.m3u8"
        video.status = 'completed'
        video.duration = duration
        video.save()

        # Очистка временных файлов
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    except Exception as e:
        logger.error(f"Ошибка при транскодировании: {str(e)}")
        try:
            video = Video.objects.get(id=id)
            video.status = 'error'

            video.save()
        except:
            pass
        raise
  


@receiver(post_save, sender=Video)
def start_transcoding(sender, instance, created, **kwargs):
    if created and instance.original_file:  # Только для новых видео
        transcode_to_hls.delay(instance.id)  # Асинхронный запуск
        instance.status = 'processing'
        instance.save()