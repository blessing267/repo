from django.shortcuts import render, redirect
from .models import Product, Message, DeliveryRequest
from .forms import ProductForm, MessageForm, DeliveryRequestForm
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from .utils import get_weather
from django.utils.translation import gettext_lazy as _

# Create your views here.
def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/home.html')

@login_required
def home_view(request):
    return render(request, 'core/home.html')

def product_list(request):
    query = request.GET.get('q')
    location = request.GET.get('location')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    category = request.GET.get('category')
    
    products = Product.objects.all().order_by('-date_posted')

    if query:
        products = products.filter(title__icontains=query)
    if location:
        products = products.filter(location__icontains=location)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    if category:
        products = products.filter(category=category)

    paginator = Paginator(products, 5)  # Show 5 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    city = location or "Ibadan"
    weather = get_weather(city)

    return render(request, 'core/product_list.html', {
        'products': page_obj,
        'query': query,
        'location': location,
        'min_price': min_price,
        'max_price': max_price,
        'category': category,
        'page_obj': page_obj,
        'weather': weather,
        
    })

@login_required
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
def inbox_view(request):
    messages = Message.objects.filter(recipient=request.user)
    return render(request, 'core/inbox.html', {'messages': messages})

@login_required
def send_message_view(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            return redirect('inbox')
    else:
        form = MessageForm()
    return render(request, 'core/send_message.html', {'form': form})

@login_required
def request_delivery(request):
    if request.method == 'POST':
        form = DeliveryRequestForm(request.POST)
        if form.is_valid():
            delivery = form.save(commit=False)
            delivery.farmer = request.user
            delivery.save()
            return redirect('my_deliveries')
    else:
        form = DeliveryRequestForm()
    return render(request, 'core/request_delivery.html', {'form': form})

@login_required
def view_pending_deliveries(request):
    if request.user.profile.role == 'logistics':
        deliveries = DeliveryRequest.objects.filter(status='pending')
        return render(request, 'core/pending_deliveries.html', {'deliveries': deliveries})
    else:
        return redirect('home')

@login_required
def accept_delivery(request, delivery_id):
    delivery = DeliveryRequest.objects.get(id=delivery_id)
    if request.user.profile.role == 'logistics':
        delivery.logistics_agent = request.user
        delivery.status = 'accepted'
        delivery.save()
        return redirect('view_deliveries')
    
@login_required
def update_delivery_status(request, delivery_id, status):
    delivery = DeliveryRequest.objects.get(id=delivery_id)
    if request.user.profile.role == 'logistics' and delivery.logistics_agent == request.user:
        delivery.status = status
        delivery.save()
        messages.success(request, f"Delivery marked as '{status}'.")
    return redirect('logistics_dashboard')

@login_required
def my_delivery_requests(request):
    if request.user.profile.role != 'farmer':
        return redirect('home')

    my_deliveries = DeliveryRequest.objects.filter(farmer=request.user)
    return render(request, 'core/my_deliveries.html', {'deliveries': my_deliveries})


@login_required
def logistics_dashboard(request):
    if request.user.profile.role != 'logistics':
        return redirect('home')

    deliveries = DeliveryRequest.objects.filter(logistics_agent=request.user)
    return render(request, 'core/logistics_dashboard.html', {'deliveries': deliveries})


