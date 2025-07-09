from config.custom_api_exceptions import PostConflictException
from rest_framework import serializers
from .models import Post, Comment
from .models import Image


class PostSerializer(serializers.ModelSerializer):
    def validate(self, data):
        if Post.objects.filter(title=data['title']).exists():
            raise PostConflictException(detail=f"A post with title: '{data['title']}' already exists.")
        return data

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
