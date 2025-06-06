from django.contrib.auth import authenticate
from ninja import NinjaAPI, Schema
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from typing import Optional

# Initialize the Ninja API
api = NinjaAPI(
    version="1.0.0",
    title="Product Management API",
    description="API for managing products and product groups, with JWT authentication."
)

# Schema for authentication request (username and password)
class AuthIn(Schema):
    username: str
    password: str

# Schema for successful authentication response (access and refresh tokens)
class AuthOut(Schema):
    access_token: str
    refresh_token: str

# Schema for API error response
class ErrorOut(Schema):
    detail: str

@api.post("/auth/token", response={200: AuthOut, 401: ErrorOut}, tags=["Authentication"])
def get_jwt_token(request, auth_in: AuthIn):
    """
    Retrieves JWT access and refresh tokens for a given username and password.
    """
    # Authenticate the user using Django's built-in authentication system
    user = authenticate(username=auth_in.username, password=auth_in.password)

    if user is not None:
        # If authentication is successful, generate access and refresh tokens
        access_token = AccessToken.for_user(user)
        refresh_token = RefreshToken.for_user(user)

        # Return the tokens
        return 200, {"access_token": str(access_token), "refresh_token": str(refresh_token)}
    else:
        # If authentication fails, return an unauthorized error
        return 401, {"detail": "Invalid credentials"}

# TODO: Add more API endpoints here later, e.g., for Product or ProductGroup management
# @api.get("/products", auth=JWTAuth(), tags=["Products"])
# def list_products(request):
#     # This endpoint would require a valid JWT token
#     return [{"id": p.id, "article": p.article} for p in Product.objects.all()]

