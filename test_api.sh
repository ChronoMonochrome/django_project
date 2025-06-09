#!/bin/bash
set -x # Print commands and their arguments as they are executed

echo "--- Starting API Endpoint Test Script ---"

# Load environment variables from .env file
# Ensure this script is run from your project root where .env resides
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "Error: .env file not found. Please run this script from your project root."
    exit 1
fi

# Define API base URL and credentials
API_BASE_URL="http://localhost:8099/api"
LOGIN_USERNAME="testuser3"
LOGIN_PASSWORD="test_password"

# --- 1. Retrieve JWT Token ---
echo -e "\n--- Attempting to retrieve JWT token ---"
TOKEN_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d "{ \"username\": \"$LOGIN_USERNAME\", \"password\": \"$LOGIN_PASSWORD\" }" \
  "${API_BASE_URL}/auth/token")

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | jq ".access_token" | cut -d ""\" -f2)

if [ -z "$ACCESS_TOKEN" ]; then
    echo "Failed to retrieve access token. Full response: $TOKEN_RESPONSE"
    echo "Please ensure the user '$LOGIN_USERNAME' exists and the password is correct."
    exit 1
fi

echo "Access Token retrieved: $ACCESS_TOKEN"


# --- 2. Test GET /get_article_crosses ---
echo -e "\n--- Testing GET /get_article_crosses ---"
curl -X GET \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "${API_BASE_URL}/get_article_crosses"
echo # Add a newline for cleaner output


# --- 3. Test POST /add_article_crosses (Add a new article) ---
echo -e "\n--- Testing POST /add_article_crosses (Adding a new unique article) ---"
NEW_ARTICLE_DATA='{
    "article": "TEST-ARTICLE-'"$(date +%s)"'",
    "brand": "TestBrand",
    "trading_numbers": "TNG-123,TNG-456",
    "description": "This is a new test product.",
    "additional_name": "For API testing",
    "product_status": "Active",
    "specifications": "Dimension: 10x10, Weight: 1kg"
}'

curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "$NEW_ARTICLE_DATA" \
  "${API_BASE_URL}/add_article_crosses"
echo # Add a newline for cleaner output

# To demonstrate conflict: Try adding the same article again (expect 409)
echo -e "\n--- Testing POST /add_article_crosses (Attempting to add duplicate article - expected 409 Conflict) ---"
DUPLICATE_ARTICLE_DATA='{
    "article": "TEST-ARTICLE-'"$(date +%s)"'",
    "brand": "TestBrand",
    "trading_numbers": "TNG-123,TNG-456",
    "description": "This is a new test product.",
    "additional_name": "For API testing",
    "product_status": "Active",
    "specifications": "Dimension: 10x10, Weight: 1kg"
}'

# Note: For robust testing, you'd capture the actual article from the first add
# and try to add it again, but for this demo, a simple duplicate attempt is fine.
# We'll use a consistent one that could realistically exist if a manual entry was made.
EXISTING_ARTICLE="SAMSUNGLCD001" # Assuming this article exists from your Excel data

EXISTING_ARTICLE_DATA_DUPLICATE='{
    "article": "'"$EXISTING_ARTICLE"'",
    "brand": "AnotherBrand",
    "trading_numbers": "XYZ-789",
    "description": "Attempting to add an existing article."
}'
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "$EXISTING_ARTICLE_DATA_DUPLICATE" \
  "${API_BASE_URL}/add_article_crosses"
echo " (Expected HTTP 409 Conflict if article '$EXISTING_ARTICLE' already exists)"
echo # Add a newline for cleaner output


# --- 4. Test POST /update_article_cross (Update an existing article) ---
echo -e "\n--- Testing POST /update_article_crosses (Updating an existing article) ---"
UPDATE_ARTICLE="SAMSUNGLCD001" # Replace with an article that definitely exists in your database
UPDATE_DATA='{
    "article": "'"$UPDATE_ARTICLE"'",
    "description": "Updated description via API script",
    "trading_numbers": "TM901,API-TEST-CROSS"
}'

curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "$UPDATE_DATA" \
  "${API_BASE_URL}/update_article_crosses"
echo # Add a newline for cleaner output

# Test update with non-existent article (expect 404)
echo -e "\n--- Testing POST /update_article_crosses (Attempting to update non-existent article - expected 404 Not Found) ---"
NON_EXISTENT_ARTICLE="NONEXISTENT-ABC-123"
NON_EXISTENT_UPDATE_DATA='{
    "article": "'"$NON_EXISTENT_ARTICLE"'",
    "description": "This article does not exist."
}'
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "$NON_EXISTENT_UPDATE_DATA" \
  "${API_BASE_URL}/update_article_crosses"
echo " (Expected HTTP 404 Not Found)"
echo # Add a newline for cleaner output

echo "--- API Endpoint Test Script Finished ---"
