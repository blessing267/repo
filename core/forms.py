from django import forms
from .models import Product, Message, DeliveryRequest
from django.utils.translation import gettext_lazy as _

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['title', 'description', 'price', 'quantity', 'location', 'category', 'image']

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['recipient', 'body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 3}),
        }
class DeliveryRequestForm(forms.ModelForm):
    class Meta:
        model = DeliveryRequest
        fields = ['product', 'pickup_location', 'destination']

