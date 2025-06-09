# Django project

This project provides a robust Django application for uploading Excel files, processing product data asynchronously, and managing it via a secure API. It leverages Celery for background tasks, Redis as a message broker, PostgreSQL for data storage, and is deployed using Bjoern as the WSGI server behind Nginx.

## Features

-   **Excel File Upload:** Easily upload product data from `.xlsx` files via a web interface.
    
-   **Asynchronous Processing:** Utilizes Celery to handle Excel file processing in the background, preventing timeouts and improving user experience.
    
-   **Product & Product Group Management:** Stores and organizes product information, including brand, article, trading numbers (crosses), descriptions, and custom specifications. Supports hierarchical product groups, with specific logic for "Автозапчасти" (Auto Parts) and its sub-groups ("Рулевое управление", "Подвеска колеса").
    
-   **User Authentication:** Includes standard user registration, login, and logout functionalities.
    
-   **JWT-Protected API:** Provides secure RESTful API endpoints for retrieving, adding, and updating product "crosses" (trading numbers), protected by JSON Web Tokens (JWT).
    
-   **Dockerized Deployment:** Full production-ready setup with Docker Compose, including containers for Django (Bjoern), Nginx, PostgreSQL, and Redis.
    

## Technologies Used

-   **Backend:** Python, Django
    
-   **WSGI Server:** Bjoern
    
-   **Reverse Proxy:** Nginx
    
-   **Database:** PostgreSQL
    
-   **Asynchronous Tasks:** Celery
    
-   **Message Broker/Backend:** Redis
    
-   **API Framework:** Django Ninja
    
-   **JWT Authentication:**  `djangorestframework-simplejwt`
    
-   **Excel Processing:** Pandas, OpenPyXL
    

## Getting Started

These instructions will get your project up and running on your local machine using Docker Compose.

### Prerequisites

Before you begin, ensure you have the following installed:

-   **Docker:**  [Install Docker Engine](https://docs.docker.com/engine/install/ "null")
    
-   **Docker Compose:**  [Install Docker Compose](https://docs.docker.com/compose/install/ "null") (usually comes with Docker Desktop)
    

### Setup

1.  **Clone the Repository:**
    
    ```
    git clone <your-repository-url>
    cd django_project # Or whatever your project root directory is named
    
    ```
    
2.  **Create `.env` file:** Create a file named `.env` in the root of your project directory (`django_project/`) and populate it with your environment variables. This file will be used by Docker Compose to configure your services.
    
    ```
    # .env
    POSTGRES_DB=django_db
    POSTGRES_USER=django_user
    POSTGRES_PASSWORD=django_password
    POSTGRES_HOST=db
    POSTGRES_PORT=5432
    DJANGO_SECRET_KEY=your_very_secret_and_long_key_for_django # IMPORTANT: CHANGE THIS IN PRODUCTION!
    DJANGO_DEBUG=True
    
    ```
    
    -   **`DJANGO_SECRET_KEY`**: Replace `your_very_secret_and_long_key_for_django` with a strong, randomly generated key. You can generate one using `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`.
        
3.  **Ensure Dockerfiles and Nginx Config are in place:** Verify that `Dockerfile.django`, `Dockerfile.nginx`, and the `nginx/nginx.conf` file (inside an `nginx` directory) are correctly placed in your project root, as detailed in the project's documentation.
    

## Running the Application with Docker Compose

Follow this sequence of commands to set up and start all services:

1.  **Build Docker Images:** This command builds the Docker images for your `web` (Django/Bjoern) and `nginx` services based on their respective Dockerfiles.
    
    ```
    docker compose build
    
    ```
    
2.  **Start Database and Redis Services:** It's crucial to start the `db` (PostgreSQL) and `redis` services first and wait for them to be fully initialized before proceeding.
    
    ```
    docker compose up -d db redis
    
    ```
    
    -   **Wait for readiness:** Allow a few moments (e.g., 10-20 seconds) for the PostgreSQL database to fully initialize and pass its health check. You can monitor its status with `docker compose ps`.
        
3.  **Run Django Migrations:** Execute Django's database migrations to create the necessary tables in your PostgreSQL database.
    
    ```
    docker compose run --rm web python manage.py makemigrations products_app
    docker compose run --rm web python manage.py migrate
    
    ```
    
4.  **Collect Static Files:** Collect all static assets (CSS, JavaScript, images) into a single directory for Nginx to serve.
    
    ```
    docker compose run --rm web python manage.py collectstatic --noinput
    
    ```
    
5.  **Create a Django Superuser (Optional but Recommended):** This allows you to access the Django admin panel. Follow the prompts to create your superuser.
    
    ```
    docker compose run --rm web python manage.py createsuperuser
    
    ```
    
6.  **Start All Services:** Finally, bring up all remaining services (the `web` Django application and `nginx` reverse proxy).
    
    ```
    docker compose up -d
    
    ```
    

### Accessing the Application

Once all services are up and running:

-   **Web Application:** Open your web browser and navigate to `http://localhost:8099/products/upload-excel/`. You will be redirected to the login page.
    
    -   You can register a new user or log in with the superuser credentials you created.
        
    -   After logging in, you can upload Excel files, and they will be processed in the background by Celery.
        
-   **API Documentation:** Access the interactive API documentation (Swagger UI) at `http://localhost:8099/api/docs`.
    
-   **Django Admin:** Access the Django administration interface at `http://localhost:8099/admin/` (login with your superuser).
    

### Stopping the Application

To stop all running Docker Compose services and remove their containers:

```
docker compose down

```

To stop services and also remove all associated volumes (including database data, static files, and media files, effectively resetting the application's data):

```
docker compose down -v

```

## Excel File Structure

The application expects an Excel file (`.xlsx`) with a single sheet and specific column headers. The headers are case-insensitive and will be normalized during processing. If the "Товарная группа" column is empty, the product will default to the "Автозапчасти" group.

**Expected Headers:**

| Бренд (Brand) | Уникальный артикул (Unique Article) | Торговые номера (Trading Numbers/Crosses) | Описание (Description) | Дополнительное описание (Additional Description) | Товарная группа (Product Group) | Статус изделия (Product Status) | Характеристики (Specifications) | | :------------ | :---------------------------------- | :------------------------------------ | :--------------------- | :-------------------------------- | :------------------------------ | :------------------------------
