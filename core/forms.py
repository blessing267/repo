from django import forms
from django.contrib.auth.models import User
from .models import Product, Message, DeliveryRequest
from django.utils.translation import gettext_lazy as _

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['title', 'description', 'price', 'quantity', 'city', 'state', 'category', 'image']

class MessageForm(forms.ModelForm):
    send_to_all = forms.BooleanField(required=False, label="Send to all users") 

    class Meta:
        model = Message
        fields = ['recipient', 'body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # make recipient optional in form
        self.fields['recipient'].required = False

class DeliveryRequestForm(forms.ModelForm):
    buyer = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name__iexact='Buyer'),
        required=True,
        label="Select Buyer"
    )

    logistics_agent = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name__iexact='Logistics'),
        required=False,  # optional at creation, can be assigned later
        label="Select Logistics Agent"
    )

    class Meta:
        model = DeliveryRequest
        fields = ['buyer', 'product', 'pickup_location', 'destination', 'logistics_agent'] 
