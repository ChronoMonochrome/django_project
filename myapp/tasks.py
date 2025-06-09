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
        current_cols = df.columns.tolist()
        rename_dict = {
            excel_col.lower(): model_field
            for excel_col, model_field in column_mapping.items()
            if excel_col.lower() in current_cols
        }
        df = df.rename(columns=rename_dict)

        # Ensure only relevant columns are kept for processing
        valid_model_fields = set(column_mapping.values())
        df = df[[col for col in df.columns if col in valid_model_fields]]

        # --- New logic for product groups ---

        # 1. Get or create the parent "Автозапчасти" group
        # This will be the default group if no other specific group is found or if it's the parent.
        auto_parts_group, created = ProductGroup.objects.get_or_create(
            name="Автозапчасти",
            defaults={'parent_id': None} # Ensure parent_id is null for the top-level group
        )
        if created:
            logger.info(f"Task {task_id}: Created new parent ProductGroup: {auto_parts_group.name}")
        else:
            logger.info(f"Task {task_id}: Found existing parent ProductGroup: {auto_parts_group.name}")

        with transaction.atomic():
            for index, row in df.iterrows():
                row_number = index + 2 # Excel rows are 1-indexed, and we start from the second row (after headers)
                self.update_state(state='PROGRESS', meta={'current_row': row_number, 'total_rows': len(df)})
                try:
                    product_group_name_from_excel = row.get('product_group_name')
                    product_group_instance = None # Initialize as None

                    # Clean product group name from excel
                    if product_group_name_from_excel and pd.notna(product_group_name_from_excel):
                        product_group_name_from_excel = str(product_group_name_from_excel).strip()
                    else:
                        product_group_name_from_excel = "" # Treat NaN or empty as empty string

                    # Determine the correct product group and its parent
                    if not product_group_name_from_excel:
                        # If group is not specified in Excel, default to "Автозапчасти"
                        product_group_instance = auto_parts_group
                        logger.info(f"Task {task_id}: Row {row_number}: No product group specified, defaulting to '{auto_parts_group.name}'.")
                    elif product_group_name_from_excel == "Автозапчасти":
                        # If it's explicitly "Автозапчасти", use the already fetched instance
                        product_group_instance = auto_parts_group
                        # Ensure its parent_id is None, in case it was somehow linked before
                        if product_group_instance.parent_id is not None:
                            product_group_instance.parent_id = None
                            product_group_instance.save()
                            logger.info(f"Task {task_id}: Updated '{product_group_instance.name}' parent_id to None.")
                    elif product_group_name_from_excel in ["Рулевое управление", "Подвеска колеса"]:
                        # For child groups, create/get them and set their parent_id
                        child_group, created = ProductGroup.objects.get_or_create(
                            name=product_group_name_from_excel
                        )
                        if created:
                            logger.info(f"Task {task_id}: Created new child ProductGroup: {child_group.name}")
                        
                        # Set or update parent_id to auto_parts_group's ID
                        if child_group.parent_id != auto_parts_group.id:
                            child_group.parent_id = auto_parts_group.id
                            child_group.save()
                            logger.info(f"Task {task_id}: Linked '{child_group.name}' to parent '{auto_parts_group.name}'.")
                        
                        product_group_instance = child_group
                    else:
                        # For any other product group name found in Excel
                        product_group_instance, created = ProductGroup.objects.get_or_create(
                            name=product_group_name_from_excel
                        )
                        if created:
                            logger.info(f"Task {task_id}: Created non-auto-related ProductGroup: {product_group_instance.name}")
                        # Other groups typically don't have a parent_id by this logic unless explicitly defined elsewhere
                        # We don't touch their parent_id if it's already set by something else.

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