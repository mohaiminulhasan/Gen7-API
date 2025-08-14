from django.db import models

class ISMDetail(models.Model):
    site_id = models.CharField(max_length=8)
    date = models.DateField()
    item_id = models.CharField(max_length=32)
    description = models.CharField(max_length=255)
    merchandise_code = models.CharField(max_length=32)
    selling_units = models.IntegerField()
    actual_sales_price = models.DecimalField(max_digits=10, decimal_places=2)
    sales_quantity = models.IntegerField()
    sales_amount = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2)
    discount_count = models.IntegerField()
    promotion_amount = models.DecimalField(max_digits=12, decimal_places=2)
    promotion_count = models.IntegerField()
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2)
    refund_count = models.IntegerField()
    transaction_count = models.IntegerField()

    class Meta:
        unique_together = ('site_id', 'date', 'item_id')
        verbose_name = "ISM Detail"
        verbose_name_plural = "ISM Details"

    def __str__(self):
        return f"{self.item_id} - {self.description}"

from django.db import models

class ItemizedInventory(models.Model):
    site_id = models.CharField(max_length=8)
    date = models.DateField()
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True)
    size = models.CharField(max_length=50, blank=True, null=True)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    external_id = models.CharField(max_length=32)
    upc = models.CharField(max_length=32, blank=True)
    image_url = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    brand = models.CharField(max_length=100, blank=True)
    unit_count = models.IntegerField()
    active = models.BooleanField(default=True)
    last_sold_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.external_id})"

    class Meta:
        # unique_together = ('site_id', 'date', 'upc')
        verbose_name = "Itemized Inventory"
        verbose_name_plural = "Itemized Inventory"