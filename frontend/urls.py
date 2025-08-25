from django.urls import path
from . import views
# from . import views_admin
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.home, name='home'),
    path('aboutUs',views.aboutUs,name="aboutUs"),
    path('contactUs',views.contactUs,name="contactUs"),
    path('error404',views.error404,name="error404"),
    path('faq',views.faq,name="faq"),
    
    #login
    path('login_user', views.login_user, name="login_user"),
    path('user-signup', views.user_signup, name="user_signup"),
    path('update_account_details', views.update_account_details, name='update_account_details'),

    path('logout_user', views.logout_user, name='logout_user'),
    
    #logout
    
    #shop
    path('shop',views.shop,name='shop'),
    path('shop/category/<slug:slug>/', views.shop_by_category, name='shop_by_category'),
    path('product-details/<slug:slug>/', views.product_details, name='product_details'),
    path('wishlist',views.wishlist,name="wishlist"),
    path('compare',views.compare,name="compare"),
    #shop
    
    #vendor
    path('single_vendor',views.single_vendor,name='single_vendor'),
    path('vendor_list',views.vendor_list,name='vendor_list'),
    path('become_a_vendor',views.become_a_vendor,name='become_a_vendor'),
    path('save-vendor', views.save_vendor, name='save_vendor'),
    #vendor
     
    #blog
    path('post_single',views.post_single,name='post_single'),
    path('blog_list',views.blog_list,name='blog_list'),
    #blog    
    
    #myaccount
    path('myAccount',views.myAccount,name="myAccount"),
    #myaccount
    
    
    #cart
    path("add/", views.add_to_cart, name="add_to_cart"),
    path('cart/', views.cart, name='cart_user'),
    path('checkout',views.order_checkout,name='order_checkout'),
    path('orderComplete',views.orderComplete,name='orderComplete'),
    path('place_order',views.place_order,name='place_order'),
    path('order_success',views.order_success,name='order_success'),
    path('update-quantity/', views.update_quantity, name='update_quantity'),
    path('remove-item/', views.remove_item, name='remove_item'),
    path('clear-cart/', views.clear_cart, name='clear_cart'),
    

    #cart
    
    # product modal
    path('quickview/<int:product_id>/', views.product_quickview, name='product_quickview'),
    
    
    # products
    path('create-product/', views.create_customer_product, name='create_customer_product')
    
]


