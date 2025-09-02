from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Message, DeliveryRequest
from .forms import ProductForm, MessageForm, DeliveryRequestForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.contrib import messages
from .utils import get_weather
from django.utils import translation
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

# Create your views here.
def home(request):
    context = {
        'LANGUAGE_CODE': translation.get_language(),
        # other context variables
    }
    return render(request, 'core/home.html', context)

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
    paginator = Paginator(products, 5)  # Show 5 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    city = location or "Ibadan"
    try:
        weather = get_weather(city)
    except Exception:
        weather = None

    return render(request, 'core/product_list.html', {
        'products': page_obj,
        'is_farmer': is_farmer,
        'query': query,
        'location': location,
        'min_price': min_price,
        'max_price': max_price,
        'category': category,
        'page_obj': page_obj,
        'weather': weather,
        
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
    return render(request, 'core/product_detail.html', {'product': product})

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
        deliveries = DeliveryRequest.objects.filter(status='pending')
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

    # Unassigned pending deliveries (available to accept)
    # unassigned_deliveries = DeliveryRequest.objects.filter(status='pending')
    
    context = {
        'assigned_deliveries': assigned_deliveries,
        # 'unassigned_deliveries': unassigned_deliveries,
        'total_deliveries': assigned_deliveries.count(),
        'pending_deliveries': assigned_deliveries.filter(status='pending').count(),
        'in_transit_deliveries': assigned_deliveries.filter(status='in_transit').count(),
        'delivered_deliveries': assigned_deliveries.filter(status='delivered').count(),
    }

    return render(request, 'core/logistics_dashboard.html', context)


