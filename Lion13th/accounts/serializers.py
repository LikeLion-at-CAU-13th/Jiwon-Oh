from rest_framework import serializers
from rest_framework_simplejwt.serializers import RefreshToken

from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=True) #default = True
    username = serializers.CharField(required=True)
    email = serializers.CharField(required=True)

    class Meta:
        model = User

        # 필요한 필드값만 지정, 회원가입은 email까지 필요
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user= User(**validated_data)
        user.set_password(password)
        user.save()

        return user

    def validate_email(self, value):
        if not "@" in value:
            raise serializers.ValidationError("Invalid email format")
        
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already existed.")
        
        return value
        
# 로그인용 시리얼라이저
class AuthSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    
    class Meta:
        model = User

        # 로그인은 username과 password만 필요
        fields = ['username', 'password']

    # 로그인 유효성 검사 함수
    def validate(self, data):
        username = data.get('username', None)
        password = data.get('password', None)

        # print("psw"+password)
		    
        # username으로 사용자 찾는 모델 함수
        user = User.get_user_by_username(username=username)
        print(user.username)
        
        # 존재하는 회원인지 확인
        if user is None:
            raise serializers.ValidationError("User does not exist.")
        else:
			      # 비밀번호 일치 여부 확인
            if not user.check_password(password):
                raise serializers.ValidationError("Wrong password.")
        
        token = RefreshToken.for_user(user)
        refresh_token = str(token)
        access_token = str(token.access_token)

        data = {
            "user": user,
            "refresh_token": refresh_token,
            "access_token": access_token,
        }

        return data
    
class OAuthSerializer(serializers.ModelSerializer):
    username = serializers.CharField()
    email = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['username','email']

    def validate(self, data):
        username = data.get('username', None)
        email = data.get('email', None)

        if email is None:
            raise serializers.ValidationError('Email does not exist.')
        
        user = User.get_user_by_email(email=email)
        
        # 존재하지 않는 회원이면 새롭게 가입
        if user is None:
            user = User.objects.create(username=username, email=email)

        token = RefreshToken.for_user(user)
        refresh_token = str(token)
        access_token = str(token.access_token)

        data = {
            "user": user,
            "refresh_token": refresh_token,
            "access_token": access_token,
        }

        return data