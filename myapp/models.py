from django.db import models

class ProductGroup(models.Model):
    name = models.CharField(max_length=255)
    parent_id = models.BigIntegerField(null=True)
    def __str__(self):
        return self.name

class Product(models.Model):
    brand = models.CharField(max_length=255)
    article = models.CharField(max_length=255, unique=True)
    trading_numbers = models.CharField(max_length=255)
    description = models.TextField()
    additional_name = models.TextField()
    product_group = models.ForeignKey(ProductGroup, on_delete=models.SET_NULL, null=True)
    product_status = models.CharField(max_length=255)
    specifications = models.TextField()
    def __str__(self):
        return self.article

