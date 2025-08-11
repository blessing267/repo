from django.urls import path, include  # ✅ This imports 'path' and 'include'
from . import views

urlpatterns = [
    path('', views.home_redirect, name='home'),
    path('products', views.product_list, name='product_list'),
    path('post/', views.product_create, name='product_create'),
    path('inbox/', views.inbox_view, name='inbox'),
    path('send-message/', views.send_message_view, name='send_message'),
    path('delivery/request/', views.request_delivery, name='request_delivery'),
    path('delivery/pending/', views.view_pending_deliveries, name='pending_deliveries'),
    path('delivery/accept/<int:delivery_id>/', views.accept_delivery, name='accept_delivery'),
    path('dashboard/logistics/', views.logistics_dashboard, name='logistics_dashboard'),
    path('delivery/update-status/<int:delivery_id>/<str:status>/', views.update_delivery_status, name='update_delivery_status'),
    path('delivery/my/', views.my_delivery_requests, name='my_deliveries'),

]