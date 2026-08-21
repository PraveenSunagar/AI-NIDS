from typing import List
from fastapi import Depends, HTTPException, status
from backend.app.models.user import User, UserRole
from backend.app.security.authentication import get_current_active_user

class RoleChecker:
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_active_user)) -> User:
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required role: {[r.value for r in self.allowed_roles]}, your role: {user.role.value}"
            )
        return user

allow_admin = RoleChecker([UserRole.ADMIN])
allow_analyst_or_admin = RoleChecker([UserRole.ADMIN, UserRole.ANALYST])
allow_all_roles = RoleChecker([UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER])
