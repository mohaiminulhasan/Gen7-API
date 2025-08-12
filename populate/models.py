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

    def __str__(self):
        return f"{self.item_id} - {self.description}"