from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import VideoViewSet, CommentViewSet, RegisterView, ChannelDetailView

router = DefaultRouter()
router.register(r'videos', VideoViewSet, basename='video')
router.register(r'videos/(?P<video_pk>\d+)/comments', CommentViewSet, basename='comment')



# urls.py
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('', include(router.urls)),
    path('channels/<slug:slug>/', ChannelDetailView.as_view(), name='channel'),
    path('token/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/register/', RegisterView.as_view(), name='register'),
 	path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
'''
curl -X POST http://localhost:8000/api/videos/ \
-H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzUyMjY5ODgyLCJpYXQiOjE3NTIyNjg1OTcsImp0aSI6IjBkNWU4MzgyYzQ1YjQ1OGE4MDdmNmY0YzViNmVkOTg5IiwidXNlcl9pZCI6Mn0.4XjH-1POBASRiyzQb9CyMN_JjfsljsmCX6IfR-Pv7RA" \
-F '{"title":"123", "file_path":"/home/ramil/Загрузки/9193185.mp4"}'


curl -v -X POST http://localhost:8000/api/videos/ \
-H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzYwODIyMzE4LCJpYXQiOjE3NjA3MzU5MTgsImp0aSI6IjMwOGUyNDdjMGVkNzQwNGNiZGQwODlhMDY3NTQ0NWQ4IiwidXNlcl9pZCI6MX0.fFs3Mbm_mMHohDfEZgB6cPjlkKHq3IU3Woq9kKkdkCY" \
-F "title=My Video" \
-F "original_file=/home/ramil/Видео/Site.mp4"

ffmpeg -i /home/ramil/Загрузки/9193185.mp4 -c:v libx264 -f hls output.m3u8



curl -o debug.log -X POST http://localhost:8000/api/videos/ \
-H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzYwODIyMzE4LCJpYXQiOjE3NjA3MzU5MTgsImp0aSI6IjMwOGUyNDdjMGVkNzQwNGNiZGQwODlhMDY3NTQ0NWQ4IiwidXNlcl9pZCI6MX0.fFs3Mbm_mMHohDfEZgB6cPjlkKHq3IU3Woq9kKkdkCY" \
-H "Content-Type: multipart/form-data" \
-F "title=Testeo" \
-F "original_file=/home/ramil/Загрузки/9193185.mp4"
'''