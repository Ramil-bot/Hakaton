from rest_framework import serializers
from .models import Video, Comment, Rating
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
            'views_count', 'likes_count', 
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

    def get_hls_url(self, obj):
        if obj.hls_path:
            return default_storage.url(obj.hls_path)
        return None

class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'text', 'created_at']
        read_only_fields = ['user']