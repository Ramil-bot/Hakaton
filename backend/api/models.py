from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils.text import slugify

class Channel(models.Model):
    # Основная информация
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='channel')
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Аватар и обложка
    avatar = models.ImageField(upload_to='channel/avatars/', blank=True, null=True)
    banner = models.ImageField(upload_to='channel/banners/', blank=True, null=True)

    # Соцсети (можно хранить как JSONField)
    social_links = models.JSONField(default=dict, blank=True)  # Пример: {"youtube": "url", "telegram": "url"}

    # Подписчики
    subscribers = models.ManyToManyField(User, related_name='subscribed_channels', blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Video(models.Model):
    owner = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='videos', null=True)
    title = models.CharField(max_length=255)
    views_count = models.PositiveIntegerField(default=0)
    original_file = models.FileField(upload_to='originals/')
    encrypted_key = models.BinaryField()  # Ключ AES-128 (16 байт)
    iv = models.BinaryField()  # Вектор инициализации (16 байт)
    hls_path = models.CharField(max_length=512, blank=True)
    status = models.CharField(max_length=20, default='uploading')
    duration = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class VideoAccess(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    expires_at = models.DateTimeField()  # Время доступа

class Comment(models.Model):    
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    status = models.BooleanField(default = False)
    created_at = models.DateTimeField(auto_now_add=True)

class Rating(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='rating')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.IntegerField()

