from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from core.forms import DeliveryRequestForm
from .models import Profile
from core.models import Product, Message, DeliveryRequest
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
import requests
from django.conf import settings

# Create your views here.
def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data.get('role')  # get role from form first
            user.profile.role = role              # then assign it
            user.profile.save()
            
            messages.success(request, "Account created successfully! You can now log in.")
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Redirect based on roleveryone to homepage
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')
    
@login_required
def dashboard_redirect(request):
    role = request.user.profile.role
    if role == 'logistics':
        return redirect('logistics_dashboard')
    elif role == 'farmer':
        return redirect('farmer_dashboard')
    elif role == 'buyer':
        return redirect('buyer_dashboard')
    else:
        return redirect('home')

@login_required
def farmer_dashboard(request):
    my_products = Product.objects.filter(farmer=request.user).order_by('-date_posted')[:5]  # latest 5
    unread_messages = Message.objects.filter(recipient=request.user, is_read=False).count()
    recent_marketplace = Product.objects.exclude(farmer=request.user).order_by('-date_posted')[:5]
    my_deliveries = DeliveryRequest.objects.filter(farmer=request.user)
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

    if request.method == 'POST':
        delivery_form = DeliveryRequestForm(request.POST)
        if delivery_form.is_valid():
            delivery = delivery_form.save(commit=False)
            delivery.farmer = request.user
            delivery.save()
            messages.success(request, "Delivery request submitted!")
            return redirect('farmer_dashboard')
    else:
        delivery_form = DeliveryRequestForm()

    return render(request, 'users/farmer_dashboard.html', {
        'my_products': my_products,
        'my_deliveries': my_deliveries,
        'unread_messages': unread_messages,
        'recent_marketplace': recent_marketplace,
        'weather': weather,
        'location': location,
        'delivery_form': delivery_form,
    })

@login_required
def buyer_dashboard(request):
    recent_products = Product.objects.all().order_by('-date_posted')[:5]
    unread_messages = Message.objects.filter(recipient=request.user, is_read=False).count()
    
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
    
    # Delivery Request
    if request.method == 'POST':
        delivery_form = DeliveryRequestForm(request.POST)
        if delivery_form.is_valid():
            delivery = delivery_form.save(commit=False)
            delivery.requester = request.user  # or .farmer for farmer
            delivery.save()
            messages.success(request, "Delivery request submitted!")
            return redirect('buyer_dashboard')
    else:
        delivery_form = DeliveryRequestForm()

    return render(request, 'users/buyer_dashboard.html', {
        'recent_products': recent_products,
        'unread_messages': unread_messages,
        'weather': weather,
        'location': location,
        'delivery_form': delivery_form,
    })
    
@login_required
def profile(request):
    profile = request.user.profile
    return render(request, 'users/profile.html', {'profile': profile})    
    
@login_required
def edit_profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, instance=request.user.profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, "Your profile has been updated!")
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    return render(request, 'users/edit_profile.html', {
        'u_form': u_form,
        'p_form': p_form
    })

def password_reset(request):
    return render(request, 'users/password_reset.html')