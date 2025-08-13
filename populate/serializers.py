from rest_framework import serializers

from .models import ISMDetail, ItemizedInventory

class ISMDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ISMDetail
        fields = '__all__'

class ItemizedInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemizedInventory
        fields = '__all__'