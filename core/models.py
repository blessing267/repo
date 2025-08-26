from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

# Create your models here.
CROP_CHOICES = [
    ('Tomato', 'Tomato'),
    ('Maize', 'Maize'),
    ('Pepper', 'Pepper'),
    ('Yam', 'Yam'),
    ('Cassava', 'Cassava'),
    ('Rice', 'Rice'),
    ('Okra', 'Okra'),
    ('Onion', 'Onion'),
    ('Cucumber', 'Cucumber'),
    ('Carrot', 'Carrot'),
    ('Eggplant', 'Eggplant'),
    ('Watermelon', 'Watermelon'),
]

class Product(models.Model):
    farmer = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(_("Title"), max_length=100)
    description = models.TextField(_("Description"))
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, default="Oyo State")
    category = models.CharField(max_length=20, choices=CROP_CHOICES, default='Tomato') 
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    date_posted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    body = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"From {self.sender} to {self.recipient}: {self.body[:30]}"
 
class DeliveryRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ] 
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="buyer_delivery_requests")
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="farmer_delivery_requests")
    logistics_agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries_handled')
    pickup_location = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_for_group = models.BooleanField(default=False)
    date_requested = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Delivery for {self.product.title} - {self.status}"    

