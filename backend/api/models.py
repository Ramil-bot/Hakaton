from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

class Video(models.Model):
	owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='videos', null=True)
	title = models.CharField(max_length=255)
	views_count = models.PositiveIntegerField(default=0)
	original_file = models.FileField(upload_to='originals/')
	encrypted_key = models.BinaryField()  # Ключ AES-128 (16 байт)
	iv = models.BinaryField()  # Вектор инициализации (16 байт)
	hls_path = models.CharField(max_length=512, blank=True)
	status = models.CharField(max_length=20, default='uploading')
	duration = models.FloatField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)

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

