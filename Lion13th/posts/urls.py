from django.urls import path
from posts.views import *

urlpatterns = [
    #path('', hello_world, name = 'hello_world'),
    #path('page', index, name='my-page'),
    #path('<int:id>', get_post_detail),

    path('', post_list, name="post_list"),
    path('<int:post_id>/', post_detail, name='post_detail'), # Post 단일 조회
    path('<int:post_id>/comments/', comment_list, name="comment_list"),
    path('category/<int:category_id>/', post_category, name="post_category"),

]