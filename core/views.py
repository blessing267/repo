from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.conf import settings

from .models import Product, Message, DeliveryRequest, CartItem, Order, OrderItem
from .forms import ProductForm, MessageForm, DeliveryRequestForm
from django.utils.translation import gettext_lazy as _
from .utils import get_weather
import requests


# Create your views here.
def home(request):
    return render(request, 'core/home.html')

def product_list(request):
    products = Product.objects.all().order_by('-date_posted')
    is_farmer = request.user.is_authenticated and request.user.groups.filter(name='Farmer').exists()

    query = request.GET.get('q')
    location = request.GET.get('location')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    category = request.GET.get('category')
    
    filters = Q()
    if query:
        filters &= Q(title__icontains=query)
    if location:
        filters &= Q(city__icontains=location) | Q(state__icontains=location)
    if min_price:
        filters &= Q(price__gte=min_price)
    if max_price:
        filters &= Q(price__lte=max_price)
    if category:
        filters &= Q(category=category)

    products = products.filter(filters)
    
    # Handle sorting
    sort = request.GET.get('sort')
    if sort == 'newest':
        products = products.order_by('-date_posted')
    elif sort == 'oldest':
        products = products.order_by('date_posted')
    elif sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    else:
        products = products.order_by('-date_posted')  # default
    
    paginator = Paginator(products, 6)  # Show 6 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    #city = location or "Ibadan"
    #try:
        #weather = get_weather(city)
    #except Exception:
        #weather = None

    return render(request, 'core/product_list.html', {
        'products': page_obj,
        'is_farmer': is_farmer,
        'query': query,
        'location': location,
        'min_price': min_price,
        'max_price': max_price,
        'category': category,
        'page_obj': page_obj,
        #'weather': weather,
        
    })


def product_create(request):
    if request.method == 'POST':
            form = ProductForm(request.POST, request.FILES)
            if form.is_valid():
                product = form.save(commit=False)
                product.farmer = request.user
                product.save()
                messages.success(request, "Product posted successfully!")
                return redirect('product_list')
            else:
                messages.error(request, "Something went wrong. Please check your form.")
    else:
        form = ProductForm()
    return render(request, 'core/product_form.html', {'form': form})

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    history = product.price_history.order_by("date_recorded")  # thanks to related_name
    return render(request, 'core/product_detail.html', {
        'product': product,
        'history': history,
    })

@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk, farmer=request.user)  # restrict to farmer who posted it
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully!")
            return redirect('product_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)
    return render(request, 'core/product_update.html', {'form': form, 'product': product})


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, farmer=request.user)  # restrict to farmer
    if request.method == 'POST':
        product.delete()
        messages.success(request, "Product deleted successfully!")
        return redirect('product_list')
    else:
        messages.error(request, "Invalid request method.")
        return redirect('product_detail', pk=pk)

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Only buyers can add to cart
    if request.user.profile.role != 'buyer':
        messages.error(request, "Only buyers can add products to the cart.")
        return redirect('product_list')

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={'quantity': 1}
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, f"{product.title} added to your cart.")
    return redirect('view_cart')

@login_required
def view_cart(request):
    if request.user.profile.role != 'buyer':
        messages.error(request, "Only buyers have a cart.")
        return redirect('product_list')

    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.get_total_price() for item in cart_items)
    return render(request, 'core/cart.html', {
        'cart_items': cart_items,
        'total': total
    })

@login_required
def remove_from_cart(request, item_id):
    if request.user.profile.role != 'buyer':
        messages.error(request, "Only buyers have a cart.")
        return redirect('product_list')

    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    cart_item.delete()
    messages.success(request, f"{cart_item.product.title} removed from your cart.")
    return redirect('view_cart')

@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if request.method == 'POST':
        if not cart_items.exists():
            messages.error(request, "Your cart is empty.")
            return redirect("product_list")

        total = sum(item.get_total_price() for item in cart_items)
        order = Order.objects.create(buyer=request.user, total_price=total)

        # Create OrderItems and notify farmers
        notified_farmers = set()
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
            )
            farmer = item.product.farmer
            if farmer.id not in notified_farmers:
                Message.objects.create(
                    sender=request.user,
                    recipient=farmer,
                    subject="New Order Notification",
                    body=f"Hi {farmer.username}, your product(s) have been purchased by {request.user.username}."
                )
                if farmer.email:
                    send_mail(
                        subject="New Order Notification",
                        message=f"Hello {farmer.username}, your product(s) have been purchased by {request.user.username}.",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[farmer.email],
                    )
                notified_farmers.add(farmer.id)

        # Empty cart
        cart_items.delete()
        messages.success(request, "Your order was placed successfully!")
        return redirect("orders")

    # GET request: just show checkout page
    total = sum(item.get_total_price() for item in cart_items)
    return render(request, 'core/checkout.html', {
        'cart_items': cart_items,
        'total': total
    })

@login_required
def orders(request):
    orders = Order.objects.filter(buyer=request.user).order_by('-created_at')
    return render(request, 'core/orders.html', {'orders': orders})


@login_required
def inbox_view(request):
    inbox_messages = Message.objects.filter(recipient=request.user)
    return render(request, 'core/inbox.html', {'inbox_messages': inbox_messages})

@login_required
def send_message_view(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            send_to_all = form.cleaned_data.get('send_to_all')
            body = form.cleaned_data.get('body')
            sender = request.user

            if send_to_all:
                # send to all users
                recipients = User.objects.exclude(id=sender.id)  # exclude yourself
                for user in recipients:
                    Message.objects.create(sender=sender, recipient=user, body=body)
                messages.success(request, "Message sent successfully to all users!")
            else:
                recipient = form.cleaned_data.get('recipient')
                if recipient:
                    Message.objects.create(sender=sender, recipient=recipient, body=body)
                    messages.success(request, f"Message sent to {recipient.username}!")
                else:
                    form.add_error('recipient', "Please select a recipient or check 'Send to all users'.")
                    return render(request, 'core/send_message.html', {'form': form})
            
            return redirect('sent_messages')
    else:
        form = MessageForm()
    return render(request, 'core/send_message.html', {'form': form})

@login_required
def sent_message_view(request):
    sent_messages = Message.objects.filter(sender=request.user).order_by('-timestamp')
    return render(request, 'core/sent_message.html', {'messages_list': sent_messages})


@login_required
def request_delivery(request, product_id):
    if request.user.profile.role != 'farmer':
        messages.error(request, "Only farmers can request deliveries.")
        return redirect('home')

    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = DeliveryRequestForm(request.POST)
        if form.is_valid():
            delivery = form.save(commit=False)
            delivery.farmer = request.user
            delivery.product = product
            delivery.status = 'pending'
            delivery.save()
            delivery.calculate_delivery_cost()  # Auto-fill delivery cost
            messages.success(request, "Delivery request submitted successfully.")
            return redirect('my_deliveries')
    else:
        form = DeliveryRequestForm()

    return render(request, 'core/request_delivery.html', {
        'form': form,
        'product': product
    })

@login_required
def view_pending_deliveries(request):
    if request.user.profile.role == 'logistics':
        deliveries = DeliveryRequest.objects.filter(
            logistics_agent=request.user
        ).exclude(status__in=['delivered', 'cancelled']) | DeliveryRequest.objects.filter(status='pending')
        deliveries = deliveries.distinct()
        return render(request, 'core/pending_deliveries.html', {'deliveries': deliveries})
    else:
        return redirect('home')

    
@login_required
def update_delivery_status(request, delivery_id, status):
    delivery = get_object_or_404(DeliveryRequest, id=delivery_id)

    allowed_statuses = ['cancelled', 'pending', 'accepted', 'in_transit', 'delivered']

    if status not in allowed_statuses:
        messages.error(request, "Invalid status update.")
        return redirect('home')

    role = request.user.profile.role

    if role == 'logistics':
        # If unassigned, allow the agent to claim it
        if delivery.logistics_agent is None:
            delivery.logistics_agent = request.user

        # Otherwise, only the assigned agent can update
        elif delivery.logistics_agent != request.user:
            messages.error(request, "You are not assigned to this delivery.")
            return redirect('logistics_dashboard')

        delivery.status = status
        delivery.save()
        messages.success(request, f"Delivery marked as '{status}'.")
        return redirect('logistics_dashboard')

    # Farmer and buyer can only cancel
    elif role == 'farmer' and delivery.farmer == request.user and status == 'cancelled':
        delivery.status = status
        delivery.save()
        messages.success(request, "Delivery request cancelled successfully.")
        return redirect('my_deliveries')

    elif role == 'buyer' and delivery.buyer == request.user and status == 'cancelled':
        delivery.status = status
        delivery.save()
        messages.success(request, "Delivery request cancelled successfully.")
        return redirect('my_deliveries')

    else:
        messages.error(request, "You are not authorized to update this delivery.")
        return redirect('home')

@login_required
def my_delivery_requests(request):
    role = request.user.profile.role

    if role == 'farmer':
        deliveries = DeliveryRequest.objects.filter(farmer=request.user)
        title = "My Delivery Requests (Farmer)"
    elif role == 'buyer':
        deliveries = DeliveryRequest.objects.filter(buyer=request.user)
        title = "My Deliveries (Buyer)"
    elif role == 'logistics':
        deliveries = DeliveryRequest.objects.all()  # logistics sees all
        title = "All Deliveries (Logistics)"
    else:
        messages.error(request, "You do not have access to deliveries.")
        return redirect('home')

    return render(request, 'core/my_deliveries.html', {
        'deliveries': deliveries,
        'title': title,
        'role': role
    })

def is_logistics(user):
    return user.is_authenticated and user.groups.filter(name='Logistics').exists()

@login_required
def logistics_dashboard(request):
    if request.user.profile.role != 'logistics':
        return redirect('home')

    # Deliveries assigned to this logistics agent
    assigned_deliveries = DeliveryRequest.objects.filter(logistics_agent=request.user)

    # Weather Data
    location = request.GET.get('city') or request.user.profile.location or "Ibadan"
    weather = None
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={settings.OPENWEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()
        if data.get("main"):
            weather = {
                "temp": data["main"]["temp"],
                "description": data["weather"][0]["description"].title(),
                "icon": data["weather"][0]["icon"]
            }
    except:
        pass
    
    context = {
        'assigned_deliveries': assigned_deliveries,
        'total_deliveries': assigned_deliveries.count(),
        'pending_deliveries': assigned_deliveries.filter(status='pending').count(),
        'in_transit_deliveries': assigned_deliveries.filter(status='in_transit').count(),
        'delivered_deliveries': assigned_deliveries.filter(status='delivered').count(),
        'weather': weather,
        'location': location,
    }

    return render(request, 'core/logistics_dashboard.html', context)


