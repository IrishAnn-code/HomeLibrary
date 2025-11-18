from fastapi import HTTPException, status


def bad_request(detail: str = "Bad request"):
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def authorization_error(detail: str = "Invalid credentials"):
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def forbidden(detail: str = "Access denied"):
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def not_found(detail: str = "Not found"):
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def conflict(detail: str = "Already exists"):
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def server_error(detail: str = "Failed to create"):
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
