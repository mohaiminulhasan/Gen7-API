from rest_framework import serializers

from .models import ISMDetail

class ISMDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ISMDetail
        fields = '__all__'