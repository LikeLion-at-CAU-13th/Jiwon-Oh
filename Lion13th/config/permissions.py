from rest_framework.permissions import BasePermission, SAFE_METHODS
from datetime import datetime, time

class IsAllowedTimeNOwerOrReadOnly(BasePermission):
    """
    작성자만 수정/삭제 가능. 읽기 권한은 모두에게 허용.
    """
    def is_blocked_time(self):
        now = datetime.now().time()
        blocked_start = time(22, 0)
        blocked_end = time(7, 0)

        if blocked_start <= now or now <= blocked_end:
            return True
        return False

    def has_permission(self, request, view):
        if self.is_blocked_time():
            return False
        return True
    
    def has_object_permission(self, request, view, obj):
        # SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS') : "읽기 전용" HTTP 메서드 목록 (리소스를 변경하지 않기 떄무네)
        if request.method in SAFE_METHODS:
            return True
        return obj.user == request.user 
