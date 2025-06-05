import pandas as pd
from celery import shared_task
from django.db import transaction
from .models import Product, ProductGroup
import os
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True) # bind=True allows access to self (the task instance)
def import_products_from_excel(self, file_path):
    """
    Celery task to import product data from an Excel file.

    Args:
        file_path (str): The absolute path to the uploaded Excel file.
    """
    task_id = self.request.id
    logger.info(f"Task {task_id}: Starting Excel import for file: {file_path}")

    try:
        # Read the Excel file into a pandas DataFrame
        # Assumes the first row contains headers.
        df = pd.read_excel(file_path, engine='openpyxl')

        # Define a mapping from expected Excel column headers (in Russian, case-insensitive)
        # to Django model field names.
        # 'товарная группа' will be specially handled as a foreign key to ProductGroup.
        column_mapping = {
            'бренд': 'brand',
            'уникальный артикул': 'article',
            'торговые номера': 'trading_numbers',
            'описание': 'description',
            'дополнительное описание': 'additional_name',
            'товарная группа': 'product_group_name', # Custom key for FK handling
            'статус изделия': 'product_status',
            'характеристики': 'specifications',
        }

        # Normalize DataFrame column names: strip whitespace and convert to lowercase
        df.columns = df.columns.str.strip().str.lower()

        # Rename columns based on the mapping
        # Create a reverse mapping for robust renaming, handling only columns that exist
        current_cols = df.columns.tolist()
        rename_dict = {
            excel_col.lower(): model_field
            for excel_col, model_field in column_mapping.items()
            if excel_col.lower() in current_cols
        }
        df = df.rename(columns=rename_dict)

        # Ensure only relevant columns are kept for processing
        # This also ensures that if some expected columns are missing, they will be skipped
        valid_model_fields = set(column_mapping.values())
        df = df[[col for col in df.columns if col in valid_model_fields]]

        # Use a transaction to ensure atomicity. If any row fails, the whole transaction can be rolled back.
        # However, here we choose to log errors and continue for individual rows.
        # For strict atomicity of the entire file, remove the inner try-except.
        with transaction.atomic():
            for index, row in df.iterrows():
                row_number = index + 2 # Excel rows are 1-indexed, and we start from the second row (after headers)
                self.update_state(state='PROGRESS', meta={'current_row': row_number, 'total_rows': len(df)})
                try:
                    product_group_name = row.get('product_group_name')
                    product_group_instance = None
                    if product_group_name and pd.notna(product_group_name):
                        # Ensure the product_group_name is a string
                        product_group_name = str(product_group_name).strip()
                        if product_group_name: # Check if it's not empty after stripping
                            product_group_instance, created = ProductGroup.objects.get_or_create(
                                name=product_group_name
                            )
                            if created:
                                logger.info(f"Task {task_id}: Created new ProductGroup: {product_group_name}")
                        else:
                            logger.warning(f"Task {task_id}: Row {row_number}: 'product_group_name' is an empty string after stripping. Product will have no group.")
                    else:
                        logger.warning(f"Task {task_id}: Row {row_number}: 'product_group_name' is missing or NaN. Product will have no group.")


                    # Prepare product data, excluding the 'product_group_name' placeholder
                    product_data = {
                        key: value for key, value in row.items()
                        if key not in ['product_group_name'] # Exclude the placeholder field
                    }

                    # Clean up data: convert NaN to empty strings and ensure all values are strings
                    for key, value in product_data.items():
                        if pd.isna(value):
                            product_data[key] = ''
                        elif not isinstance(value, str):
                            product_data[key] = str(value)

                    # Add the ProductGroup foreign key instance
                    product_data['product_group'] = product_group_instance

                    # Check for 'article' as it's unique and required for update_or_create
                    if 'article' not in product_data or not product_data['article']:
                        logger.error(f"Task {task_id}: Row {row_number}: 'article' is missing or empty. Skipping product creation/update.")
                        continue # Skip to the next row if article is missing

                    # Create or update Product instance using 'article' as the unique identifier
                    product, created = Product.objects.update_or_create(
                        article=product_data['article'],
                        defaults=product_data
                    )
                    if created:
                        logger.info(f"Task {task_id}: Created new Product: {product.article}")
                    else:
                        logger.info(f"Task {task_id}: Updated existing Product: {product.article}")

                except KeyError as e:
                    logger.error(f"Task {task_id}: Row {row_number}: Missing expected column: {e}. Row data: {row.to_dict()}")
                except Exception as e:
                    logger.error(f"Task {task_id}: Error processing row {row_number}: {e}. Row data: {row.to_dict()}")
                    # Continue to the next row even if one fails
                    continue

        logger.info(f"Task {task_id}: Successfully processed Excel file: {file_path}")

    except FileNotFoundError:
        logger.error(f"Task {task_id}: Error: File not found at {file_path}")
    except pd.errors.EmptyDataError:
        logger.error(f"Task {task_id}: Error: The Excel file {file_path} is empty.")
    except Exception as e:
        logger.exception(f"Task {task_id}: An unexpected error occurred during Excel processing for file {file_path}: {e}")
    finally:
        # Clean up the temporary file after processing
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Task {task_id}: Cleaned up temporary file: {file_path}")


