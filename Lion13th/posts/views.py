from django.shortcuts import render
from django.http import JsonResponse # 추가 
from django.shortcuts import get_object_or_404 # 추가
from django.views.decorators.http import require_http_methods # 추가
from .models import *
import json
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from config.permissions import IsAllowedTimeNOwerOrReadOnly

from .serializers import PostSerializer, CommentSerializer

# APIView를 사용하기 위해 import
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404

from django.core.files.storage import default_storage  
from .serializers import ImageSerializer
from django.conf import settings
import boto3

#swagger
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import uuid #image 마다 고유 id 넣을 수 있도록 
from rest_framework.parsers import MultiPartParser, FormParser #세션2 오류 해결용..


class PostList(APIView):
    def post(self, request, format=None):
        user_id = request.data.get('user')
        user = get_object_or_404(User, pk=user_id)

        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)  # user 객체 직접 전달!
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, format=None):
        posts = Post.objects.all()
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)
    
class PostDetail(APIView):
    permission_classes = [IsAllowedTimeNOwerOrReadOnly]

    def get_object(self, post_id): 
        return get_object_or_404(Post, id=post_id)

    def get(self, request, post_id):
        post = self.get_object(post_id)
        self.check_object_permissions(request, post)
        serializer = PostSerializer(post)
        return Response(serializer.data)
    
    def put(self, request, post_id):
        post = self.get_object(post_id)
        self.check_object_permissions(request, post) #권한체크

        serializer = PostSerializer(post, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, post_id):
        post = self.get_object(post_id)
        self.check_object_permissions(request, post) #권한체크

        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class CommentList(APIView):
    def post(self, request, post_id, format=None):
        # URL의 post_id를 body에 강제로 삽입 <- id 안넣어도 됨
        data = request.data.copy()
        data['post'] = post_id

        serializer = CommentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        comments = Comment.objects.filter(post=post)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)


# 함수 데코레이터, 특정 http method만 허용
@require_http_methods(["POST","GET"])
def post_list(request):
    
    if request.method == "POST":
    
        # byte -> 문자열 -> python 딕셔너리
        body = json.loads(request.body.decode('utf-8'))
    
		# 프론트에게서 user id를 넘겨받는다고 가정.
		# 외래키 필드의 경우, 객체 자체를 전달해줘야하기 때문에
        # id를 기반으로 user 객체를 조회해서 가져옵니다 !
        user_id = body.get('user')
        user = get_object_or_404(User, pk=user_id)

	    # 새로운 데이터를 DB에 생성
        new_post = Post.objects.create(
            title = body['title'],
            content = body['content'],
            status = body['status'],
            user = user
        )
    
	    # Json 형태 반환 데이터 생성
        new_post_json = {
            "id": new_post.id,
            "title" : new_post.title,
            "content": new_post.content,
            "status": new_post.status,
            "user": new_post.user.id
        }

        return JsonResponse({
            'status': 200,
            'message': '게시글 생성 성공',
            'data': new_post_json
        })

    if request.method == "GET":
        post_all = Post.objects.all()
    
		# 각 데이터를 Json 형식으로 변환하여 리스트에 저장
        post_json_all = []
        
        for post in post_all:
            post_json = {
                "id": post.id,
                "title" : post.title,
                "content": post.content,
                "status": post.status,
                "user": post.user.id
            }
            post_json_all.append(post_json)

        return JsonResponse({
            'status': 200,
            'message': '게시글 목록 조회 성공',
            'data': post_json_all
        })

@require_http_methods(["GET", "PATCH", "DELETE"])
def post_detail(request, post_id):

    # post_id에 해당하는 단일 게시글 조회
    if request.method == "GET":
        try:
            post=Post.objects.get(id=post_id)
            post_detail_json = {
                "id" : post.id,
                "title" : post.title,
                "content" : post.content,
                "status" : post.status,
                "user" : post.user.username
            }
            return JsonResponse({
                "status" : 200,
                "data": post_detail_json})
        except Post.DoesNotExist:
            raise PostNotFoundException

    

    if request.method == "PATCH":
        body = json.loads(request.body.decode('utf-8'))
        
        update_post = get_object_or_404(Post, pk=post_id)

        if 'title' in body:
            update_post.title = body['title']
        if 'content' in body:
            update_post.content = body['content']
        if 'status' in body:
            update_post.status = body['status']
    
        update_post.save()

        update_post_json = {
            "id": update_post.id,
            "title" : update_post.title,
            "content": update_post.content,
            "status": update_post.status,
            "user": update_post.user.id,
        }

        return JsonResponse({
            'status': 200,
            'message': '게시글 수정 성공',
            'data': update_post_json
        })
        
    if request.method == "DELETE":
        delete_post = get_object_or_404(Post, pk=post_id)
        delete_post.delete()

        return JsonResponse({
                'status': 200,
                'message': '게시글 삭제 성공',
                'data': None
        })

# 과제 - comment 테이블 API 만들기
@require_http_methods(["GET"])
def comment_list(request, post_id):
    
    if request.method == "GET":
        comment_all = Comment.objects.filter(post_id=post_id) 

        comment_json_all = []

        for comment in comment_all:
            comment_json = {
                "id" : comment.id,
                "writer" : comment.writer,
                "content" : comment.content,
                "post" : comment.post.id
            }
            comment_json_all.append(comment_json)

        return JsonResponse({
            'status' : 200,
            'message' : '댓글 목록 조회 성공',
            'data' : comment_json_all
        })

#카테고리별 게시글 조회
@require_http_methods(["GET"])
def post_category(request, category_id):

    posts = PostCategory.objects.filter(category_id=category_id).select_related('post').order_by('-post__created')

    post_json_all = []

    for ps in posts:
        post=ps.post
        post_json = {
            "id": post.id,
            "title" : post.title,
            "content" : post.content,
            "status" : post.status,
            "user" : post.user.id,
            "category" : category_id
        }
        post_json_all.append(post_json)
    return JsonResponse({
        'status': 200,
        'message': '카테고리별 게시글 조회 완료',
        'data': post_json_all
    })


def hello_world(request):
    if request.method == "GET":
        return JsonResponse({
            'status' : 200,
            'data' : "Hello likelion-13th!"
        })

def index(request):
    return render(request, 'index.html')

### imageupload ### 
class ImageUploadView(APIView):
    def post(self, request):
        if 'image' not in request.FILES:
            return Response({"error": "No image file"}, status=status.HTTP_400_BAD_REQUEST)

        image_file = request.FILES['image']

        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )

        # file_path = f"uploads/{image_file.name}"
        # S3에 파일 저장 -> 저장할 때마다 고유 id 
        unique_filename = f"{uuid.uuid4()}_{image_file.name}"
        file_path = f"uploads/{unique_filename}"

        # S3에 파일 업로드
        try:
            s3_client.put_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=file_path,
                Body=image_file.read(),
                ContentType=image_file.content_type,
            )
        except Exception as e:
            return Response({"error": f"S3 Upload Failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 업로드된 파일의 URL 생성
        image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{file_path}"

        # DB에 저장
        image_instance = Image.objects.create(image_url=image_url)
        serializer = ImageSerializer(image_instance)


        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
##### Swagger #####

class PostList(APIView):
    @swagger_auto_schema(
        operation_summary="게시글 생성",
        operation_description="새로운 게시글을 생성합니다.",
        request_body=PostSerializer,
        responses={201: PostSerializer, 400: "잘못된 요청"}
    )
    def post(self, request, format=None):
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="게시글 목록 조회",
        operation_description="모든 게시글을 조회합니다.",
        responses={200: PostSerializer(many=True)}
    )
    def get(self, request, format=None):
        posts = Post.objects.all()
	    # 많은 post들을 받아오려면 (many=True) 써줘야 한다!
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)
    
## 과제 2 image
class ImageUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]  # ✅ 이것 추가

    @swagger_auto_schema(
        operation_summary="이미지 업로드",
        operation_description="이미지 파일을 S3에 업로드하고 URL을 반환합니다.",
        manual_parameters=[
            openapi.Parameter(
                'image',
                openapi.IN_FORM,
                description="업로드할 이미지 파일",
                type=openapi.TYPE_FILE,
                required=True
            )
        ],
        responses={201: ImageSerializer}
    )
    def post(self, request):
        if 'image' not in request.FILES:
            return Response({"error": "No image file"}, status=status.HTTP_400_BAD_REQUEST)

        image_file = request.FILES['image']

        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )

        unique_filename = f"{uuid.uuid4()}_{image_file.name}"
        file_path = f"uploads/{unique_filename}"

        try:
            s3_client.put_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=file_path,
                Body=image_file.read(),
                ContentType=image_file.content_type,
            )
        except Exception as e:
            return Response({"error": f"S3 Upload Failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{file_path}"
        image_instance = Image.objects.create(image_url=image_url)
        serializer = ImageSerializer(image_instance)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

## 과제2 - post 부분
class PostDetail(APIView):
    permission_classes = [IsAllowedTimeNOwerOrReadOnly]

    @swagger_auto_schema(
        operation_summary="단일 게시글 조회",
        responses={200: PostSerializer}
    )
    def get(self, request, post_id):
        post = self.get_object(post_id)
        self.check_object_permissions(request, post)
        serializer = PostSerializer(post)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="게시글 수정",
        request_body=PostSerializer,
        responses={200: PostSerializer, 400: "잘못된 요청"}
    )
    def put(self, request, post_id):
        post = self.get_object(post_id)
        self.check_object_permissions(request, post)
        serializer = PostSerializer(post, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="게시글 삭제",
        responses={204: "삭제 성공"}
    )
    def delete(self, request, post_id):
        post = self.get_object(post_id)
        self.check_object_permissions(request, post)
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
