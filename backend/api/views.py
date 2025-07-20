from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from .models import Video, Comment, Rating
from .serializers import VideoSerializer, CommentSerializer
from .permissions import IsOwnerOrReadOnly
from rest_framework.parsers import MultiPartParser
from rest_framework_simplejwt.tokens import RefreshToken
from .pagination import CustomPagination
from .tasks import transcode_to_hls

class VideoViewSet(viewsets.ModelViewSet):
    parser_classes = [MultiPartParser]
    queryset = Video.objects.select_related('owner').prefetch_related('comments')
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['owner', 'created_at']
    pagination_class = CustomPagination

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        video = self.get_object()
        Rating.objects.create(video=video, user=request.user, value=1)
        return Response({'status': 'liked'}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        video = self.get_object()
        comments = video.comments.all().select_related('user')
        page = self.paginate_queryset(comments)
        serializer = CommentSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        # В ответе будет ID видео, по которому можно проверять статус
        return response

    def perform_create(self, serializer):
        video = serializer.save(owner=self.request.user)
        
        # Сохраняем оригинальный файл
        # print(self.request.FILES.keys())
        # video_file = self.request.FILES['original_file']
        # file_path = default_storage.save(f'originals/{video.id}_{video_file.name}', video_file)
        
        # Запускаем асинхронную обработку
        transcode_to_hls.delay(video.id)

class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Comment.objects.filter(video_id=self.kwargs['video_pk', ])

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            video_id=self.kwargs['video_pk']
        )
        
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('moderation'):
            if self.request.user.has_perm('api.moderate_comment'):
                return qs.filter(status='pending')
        return qs.filter(video=self.kwargs['video_pk'])

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticatedOrReadOnly])
    def moderate(self, request, pk=None):
        comment = self.get_object()
        serializer = CommentModerationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if not request.user.has_perm('api.moderate_comment'):
            return Response({'error': 'Нет прав на модерацию'}, status=403)

        comment.status = serializer.validated_data['status']
        comment.moderator = request.user
        comment.moderated_at = timezone.now()
        comment.save()
        
        return Response({'status': 'Статус обновлен'})


class RegisterView(APIView):
    User = get_user_model()
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email', '')

        if not username or not password:
            return Response(
                {"error": "Требуется имя пользователя и пароль"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if self.User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

        if email != '' and (email and self.User.objects.filter(email=email).exists()):
            return Response(
                {"error": "Email уже используется"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = self.User.objects.create_user(
            username=username,
            password=password,
            email=email,
            is_active=True  # Убедитесь, что пользователь активен
        )

        if not user.is_authenticated:
            return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)
        Refresh = RefreshToken.for_user(user)

        return Response({"success": "User created successfully", 'refresh':str(Refresh), 'access': str(Refresh.access_token)}, status=status.HTTP_201_CREATED)
