from django.contrib.auth import authenticate
from ninja import NinjaAPI, Schema
from ninja.security import HttpBearer # Import HttpBearer for JWT authentication
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from typing import Optional, List
from django.shortcuts import get_object_or_404
from myapp.models import Product # Import your Product model
import logging

logger = logging.getLogger(__name__)

# Initialize the Ninja API
api = NinjaAPI(
    version="1.0.0",
    title="Product Management API",
    description="API for managing products and product groups, with JWT authentication."
)

# Custom authentication class for JWT using HttpBearer
class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            # Validate the token using Simple JWT's built-in validation
            # This will raise an exception if the token is invalid or expired
            from rest_framework_simplejwt.authentication import JWTAuthentication
            validated_token = JWTAuthentication().get_validated_token(token)
            user = JWTAuthentication().get_user(validated_token)
            if user and user.is_active:
                request.auth_user = user # Attach user to request for potential use in endpoints
                return user
        except Exception as e:
            logger.error(f"JWT authentication failed: {e}")
            return None # Authentication failed

# Schemas for authentication request (username and password)
class AuthIn(Schema):
    username: str
    password: str

# Schemas for successful authentication response (access and refresh tokens)
class AuthOut(Schema):
    access_token: str
    refresh_token: str

# Schema for API error response
class ErrorOut(Schema):
    detail: str

# Schema for "Article Crosses" output
class ArticleCrossesOut(Schema):
    article: str
    brand: str
    trading_numbers: str # Assuming "кроссы" are stored as a string in trading_numbers

# Schema for adding a new article with crosses
class AddArticleCrossIn(Schema):
    article: str
    brand: str
    trading_numbers: Optional[str] = ""
    description: Optional[str] = ""
    additional_name: Optional[str] = ""
    product_status: Optional[str] = ""
    specifications: Optional[str] = ""

# Schema for updating an existing article with crosses
class UpdateArticleCrossIn(Schema):
    article: str
    brand: Optional[str] = None
    trading_numbers: Optional[str] = None
    description: Optional[str] = None
    additional_name: Optional[str] = None
    product_status: Optional[str] = None
    specifications: Optional[str] = None


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


@api.get("/get_article_crosses", response={200: List[ArticleCrossesOut], 401: ErrorOut}, auth=JWTAuth(), tags=["Articles and Crosses"])
def get_article_crosses(request):
    """
    Returns articles, brands, and their crosses (trading numbers).
    Requires JWT authentication.
    """
    # request.auth will contain the authenticated user if JWTAuth was successful
    # print(f"Authenticated user for GET /get_article_crosses: {request.auth.username}")
    
    products = Product.objects.all().values('article', 'brand', 'trading_numbers')
    return list(products)


@api.post("/add_article_crosses", response={201: ArticleCrossesOut, 400: ErrorOut, 401: ErrorOut, 409: ErrorOut}, auth=JWTAuth(), tags=["Articles and Crosses"])
def add_article_crosses(request, data: AddArticleCrossIn):
    """
    Adds a new article and its crosses.
    If the article already exists, it returns a 409 Conflict.
    Requires JWT authentication.
    """
    # print(f"Authenticated user for POST /add_article_crosses: {request.auth.username}")
    
    if Product.objects.filter(article=data.article).exists():
        return 409, {"detail": f"Article '{data.article}' already exists."}

    try:
        product = Product.objects.create(
            article=data.article,
            brand=data.brand,
            trading_numbers=data.trading_numbers,
            description=data.description,
            additional_name=data.additional_name,
            product_status=data.product_status,
            specifications=data.specifications,
            # product_group is nullable, so we don't need to pass it if not provided
        )
        return 201, product
    except Exception as e:
        logger.error(f"Error adding article cross: {e}", exc_info=True)
        return 400, {"detail": f"Failed to add article: {e}"}


@api.post("/update_article_crosses", response={200: ArticleCrossesOut, 400: ErrorOut, 401: ErrorOut, 404: ErrorOut}, auth=JWTAuth(), tags=["Articles and Crosses"])
def update_article_crosses(request, data: UpdateArticleCrossIn):
    """
    Updates an existing article and its crosses.
    If the article does not exist, it returns a 404 Not Found.
    Requires JWT authentication.
    """
    # print(f"Authenticated user for POST /update_article_crosses: {request.auth.username}")

    product = get_object_or_404(Product, article=data.article)

    # Update fields only if they are provided in the request body (not None)
    if data.brand is not None:
        product.brand = data.brand
    if data.trading_numbers is not None:
        product.trading_numbers = data.trading_numbers
    if data.description is not None:
        product.description = data.description
    if data.additional_name is not None:
        product.additional_name = data.additional_name
    if data.product_status is not None:
        product.product_status = data.product_status
    if data.specifications is not None:
        product.specifications = data.specifications

    try:
        product.save()
        return 200, product
    except Exception as e:
        logger.error(f"Error updating article cross: {e}", exc_info=True)
        return 400, {"detail": f"Failed to update article: {e}"}
