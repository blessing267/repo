from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('products', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('product/<int:pk>/edit/', views.product_update, name='product_update'),
    path('product/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('post/', views.product_create, name='product_create'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/checkout/', views.checkout, name='checkout'),
    path('orders/', views.orders, name='orders'),
    path('inbox/', views.inbox_view, name='inbox'),
    path('send_message/', views.send_message_view, name='send_message'),
    path('messages_list/sent/', views.sent_message_view, name='sent_messages'),

    # Delivery URLs
    path('delivery/request/<int:product_id>/', views.request_delivery, name='request_delivery_with_product'),
    path('delivery/pending/', views.view_pending_deliveries, name='pending_deliveries'),
    path('delivery/update-status/<int:delivery_id>/<str:status>/', views.update_delivery_status, name='update_delivery_status'),
    path('delivery/my/', views.my_delivery_requests, name='my_deliveries'),

    # Logistics dashboard
    path('dashboard/logistics/', views.logistics_dashboard, name='logistics_dashboard'),
    
    # your other urls...
    path('i18n/', include('django.conf.urls.i18n')),
]
