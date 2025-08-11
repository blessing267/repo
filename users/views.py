from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegisterForm
from .models import Profile
from core.models import Product, Message
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
            role = form.cleaned_data.get('role')
            Profile.objects.create(user=user, role=role)
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

            # Redirect based on role
            profile, created = Profile.objects.get_or_create(user=user)
            if profile.role == 'farmer':
                return redirect('farmer_dashboard')
            elif profile.role == 'buyer':
                return redirect('buyer_dashboard') 
            elif profile.role == 'logistics':
                return redirect('logistics_dashboard')
            else:
                messages.warning(request, "Role not recognized. Redirecting to homepage.")
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
    if request.user.profile.role == 'farmer':
        return redirect('farmer_dashboard')
    else:
        return redirect('buyer_dashboard')

@login_required
def farmer_dashboard(request):
    my_products = Product.objects.filter(farmer=request.user).order_by('-date_posted')[:5]  # latest 5
    unread_messages = Message.objects.filter(recipient=request.user, is_read=False).count()
    recent_marketplace = Product.objects.exclude(farmer=request.user).order_by('-date_posted')[:5]
    
    # Weather Data
    location = request.user.profile.location or "Ibadan"  # default
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

    return render(request, 'users/farmer_dashboard.html', {
        'my_products': my_products,
        'unread_messages': unread_messages,
        'recent_marketplace': recent_marketplace,
        'weather': weather,
        'location': location
    })

@login_required
def buyer_dashboard(request):
    recent_products = Product.objects.all().order_by('-date_posted')[:5]
    unread_messages = Message.objects.filter(recipient=request.user, is_read=False).count()
    
    # Weather Data
    location = request.user.profile.location or "Ibadan"  # default location if not set
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
    
    return render(request, 'users/buyer_dashboard.html', {
        'recent_products': recent_products,
        'unread_messages': unread_messages,
        'weather': weather,
        'location': location
    })