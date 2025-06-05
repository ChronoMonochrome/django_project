import os
from django.shortcuts import render, redirect
from django.conf import settings
from .forms import ExcelUploadForm
from .tasks import import_products_from_excel
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)

def upload_excel_view(request):
    """
    Handles Excel file upload form submission.
    """
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']

            # Ensure the 'media' directory exists within your project root
            # defined by MEDIA_ROOT in settings.py
            if not os.path.exists(settings.MEDIA_ROOT):
                os.makedirs(settings.MEDIA_ROOT)
                logger.info(f"Created MEDIA_ROOT directory: {settings.MEDIA_ROOT}")

            # Define a unique temporary path to save the file
            # Using excel_file.name directly might lead to conflicts if multiple files
            # with the same name are uploaded. A UUID would be more robust.
            file_name = excel_file.name
            file_path = os.path.join(settings.MEDIA_ROOT, file_name)

            # In case a file with the same name already exists (from a previous upload),
            # append a timestamp or UUID to make it unique.
            # For simplicity, we are overwriting, but for production, use a unique filename.
            # Example for unique filename:
            # from uuid import uuid4
            # unique_filename = f"{uuid4()}_{file_name}"
            # file_path = os.path.join(settings.MEDIA_ROOT, unique_filename)

            # Save the uploaded file chunks
            try:
                with open(file_path, 'wb+') as destination:
                    for chunk in excel_file.chunks():
                        destination.write(chunk)
                logger.info(f"File saved temporarily to: {file_path}")
            except IOError as e:
                logger.error(f"Failed to save uploaded file {file_name} to {file_path}: {e}")
                messages.error(request, 'Failed to save the uploaded file on the server.')
                return render(request, 'products_app/upload_excel.html', {'form': form})


            # Enqueue the Celery task
            # .delay() is a shortcut for .apply_async()
            try:
                import_products_from_excel.delay(file_path)
                messages.success(request, 'Excel file uploaded successfully! Processing started in the background.')
                logger.info(f"Celery task 'import_products_from_excel' enqueued for file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to enqueue Celery task for {file_path}: {e}")
                messages.error(request, 'Failed to start background processing. Please try again.')

            return redirect('upload_excel') # Redirect to the same page or another success page
        else:
            # Form is not valid, display errors
            messages.error(request, 'Error uploading file. Please correct the form errors.')
            logger.warning(f"Form validation failed: {form.errors}")
    else:
        form = ExcelUploadForm()
    return render(request, 'products_app/upload_excel.html', {'form': form})
