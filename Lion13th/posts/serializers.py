from config.custom_api_exceptions import PostConflictException, DailyPostLimitException
from rest_framework import serializers
from .models import Post, Comment
from .models import Image
from datetime import datetime
# from django.contrib.auth import get_user_model # 사용자 id 확인할 때 쓰이는 것

# User = get_user_model()

class PostSerializer(serializers.ModelSerializer):
    def validate(self, data):
        if Post.objects.filter(title=data['title']).exists():
            raise PostConflictException(detail=f"A post with title: '{data['title']}' already exists.")
        return data

    def create(self, validated_data):
        user = validated_data.get('user')
        today = datetime.now().date()

        if Post.objects.filter(user=user, created__date=today).exists():
            raise DailyPostLimitException()

        return super().create(validated_data)

    class Meta:
        model = Post
        fields = "__all__"



class CommentSerializer(serializers.ModelSerializer):
    def validate_content(self, value):
        if len(value.strip()) < 15:
            raise serializers.ValidationError("댓글은 최소 15자 이상!!")
        return value

    class Meta:
        model = Comment
        fields = "__all__"


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = "__all__"
