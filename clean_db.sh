#!/bin/bash

# Load environment variables from .env file
# Ensure this script is run from your project root where .env resides
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "Error: .env file not found. Please run this script from your project root."
    exit 1
fi

DB_NAME="${POSTGRES_DB}"
DB_USER="${POSTGRES_USER}"
DB_PASSWORD="${POSTGRES_PASSWORD}"
DB_HOST="db" # Service name as defined in docker-compose.yml
DB_PORT="5432"

TABLE_TO_TRUNCATE="myapp_product" # Name of the table to truncate

echo "Attempting to truncate table '${TABLE_TO_TRUNCATE}' in database '${DB_NAME}'..."

# Execute the TRUNCATE command inside the 'db' Docker container
# We use PGPASSWORD for non-interactive password passing, which is suitable for scripts.
# The -h db argument ensures psql connects to the 'db' service within the Docker network.
docker compose exec -T db psql \
  -h "${DB_HOST}" \
  -p "${DB_PORT}" \
  -U "${DB_USER}" \
  -d "${DB_NAME}" \
  -c "TRUNCATE TABLE \"${TABLE_TO_TRUNCATE}\" RESTART IDENTITY CASCADE;"

# Explanation of SQL TRUNCATE options:
# TRUNCATE TABLE "table_name": Deletes all rows from the table.
# RESTART IDENTITY: Resets any sequence generators (like auto-incrementing IDs)
#                   associated with the table's columns back to their starting values.
# CASCADE: Automatically truncates all tables that have foreign-key references
#          to the specified table, and so on. Use with caution if you only
#          intend to clear one table and its dependents. If you only want to truncate
#          this specific table and not its dependents, remove CASCADE.
#          Given your schema, 'Product' has a ForeignKey to 'ProductGroup'.
#          If 'ProductGroup' had a foreign key to 'Product' (circular), CASCADE would be needed.
#          For just truncating `products_app_product`, CASCADE is likely not strictly
#          necessary unless other tables directly reference `products_app_product`'s ID.
#          However, it's a good habit if you intend a full reset of related data.

if [ $? -eq 0 ]; then
    echo "Successfully truncated table '${TABLE_TO_TRUNCATE}'."
else
    echo "Failed to truncate table '${TABLE_TO_TRUNCATE}'. Check the logs above for errors."
fi
