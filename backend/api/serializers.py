from rest_framework import serializers
from .models import Video, Comment, Rating, Channel, VideoThumbnail
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class VideoSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    is_owner = serializers.SerializerMethodField()
    likes_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Video
        fields = [
            'id', 'title', 'owner', 'original_file', 'is_owner', 
            'duration', 'created_at', 'hls_path',
            'views_count', 'likes_count', 'thumbnail'
        ]
        # 'thumbnail'
        extra_kwargs = {'hls_path': {'read_only': True}}

    def get_is_owner(self, obj):
        request = self.context.get('request')
        return request.user == obj.owner

    def validate_title(self, value):
        if len(value) < 5:
            raise serializers.ValidationError("Title too short (min 5 chars)")
        return value

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)

    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None

    def get_hls_url(self, obj):
        if obj.hls_path:
            request = self.context.get('request')
            if request:
                # Предполагая, что hls_path хранится относительно media
                return request.build_absolute_uri(f'/media/{obj.hls_path}')
            return f'/media/{obj.hls_path}'
        return None
    def get_status(self, obj):
        if obj.status !='completed':
            return True

class ChannelSerializer(serializers.ModelSerializer):
    videos = VideoSerializer(many=True, read_only=True)
    subscriber_count = serializers.SerializerMethodField()

    class Meta:
        model = Channel
        fields = ['id', 'name', 'slug', 'description', 'avatar', 'banner', 'subscriber_count', 'videos']

    def get_subscriber_count(self, obj):
        return obj.subscribers.count()

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'video', 'user', 'text', 'status', 'created_at']
        read_only_fields = ['user', 'moderated_at', 'moderator']

class CommentModerationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'status', 'moderator_notes']
        extra_kwargs = {
            'status': {'required': True},
        }

class VideoThumbnailSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = VideoThumbnail
        fields = ['id', 'image', 'image_url', 'timestamp', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

