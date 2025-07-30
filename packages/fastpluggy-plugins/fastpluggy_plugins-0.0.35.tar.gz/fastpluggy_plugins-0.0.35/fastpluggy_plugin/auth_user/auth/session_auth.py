# core/auth/session_auth.py
from abc import ABC
from typing import Optional, Tuple

from fastapi import Request, status, HTTPException
from fastpluggy.core.auth.auth_interface import AuthInterface
from fastpluggy.core.database import get_db
from starlette.authentication import AuthCredentials, BaseUser

from ..models import Session


class SessionAuthManager(AuthInterface, ABC):
    login_redirect: bool = True
    login_url: str = "/login"
    logout_url: str = "/logout"

    async def on_authenticate_error(self, request: Request):
        if self.login_redirect:
            raise HTTPException(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                detail="Not authenticated",
                headers={"Location": self.login_url}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )

    async def authenticate(self, request: Request) -> Optional[Tuple[BaseUser, AuthCredentials]]:
        # Retrieve the session ID from the cookie.
        session_id = request.cookies.get("session")
        if not session_id:
            # No session cookie provided; authentication not provided.
            return None

        # Retrieve the database session.
        db = next(get_db())

        # Query the sessions table for a matching session record.
        session_record = db.query(Session).filter(Session.session_id == session_id).first()
        if not session_record:
            # No session record found; authentication fails.
            return None

        # Extract the user_id from the session data.
        # Assumes that sess_data is a JSON column with a key "user_id".
        user_id = session_record.session_data.get("user_id")
        if not user_id:
            # Session exists but no user_id found.
            return None

        # Retrieve the user from the user table.
        user = db.query(self.user_model).get(user_id)
        if not user:
            # User not found; authentication fails.
            return None

        # Return the authenticated user and associated credentials.
        return AuthCredentials(["authenticated"]), user

    # async def authenticate(self, request: Request) -> FastPluggyBaseUser:
    #     user_id = request.session.get("user_id")
    #     if not user_id:
    #         return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    #     db: Session = next(get_db())
    #     user = db.query(FastPluggyBaseUser).get(user_id)
    #     if not user:
    #         return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    #     return user
    # async def authenticate(self, request: Request) -> Optional[Tuple[BaseUser, AuthCredentials]]:
    #     # Retrieve user ID from the session.
    #     user_id = request.session.get("user_id")
    #     if not user_id:
    #         # No user id found; authentication not provided.
    #         return None
    #
    #     # Retrieve the database session.
    #     # Adjust this according to how your application attaches a DB session.
    #     db: Session = next(get_db())
    #     user = db.query(User).get(user_id)
    #     if not user:
    #         # User not found; authentication fails.
    #         return None
    #
    #     # If a user is found, return a tuple of ( credentials, user )
    #     return AuthCredentials(["authenticated"]), user
