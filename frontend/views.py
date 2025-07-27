from django.shortcuts import render, redirect
from django.contrib import messages
from smart.models import *

# Create your views here.


def home(request):
    return render(request, 'front/index.html')


def aboutUs(request):
    header=AboutusPageHeader.objects.filter(is_active=True).first()
    context={
        'header':header
    }
    return render(request, 'front/pages/about-us.html',context)


def contactUs(request):
    faqs = contactFAQ.objects.filter(is_active=True).order_by('order')
    header = contactPageHeader.objects.filter(is_active=True).first()
    locations = ContactLocation.objects.all()
    if request.method == 'POST':
        name = request.POST.get('username')
        email = request.POST.get('email_1')
        phone = request.POST.get('phone')
        message = request.POST.get('message')

        if name and email and message:
            ContactMessage.objects.create(
                name=name,
                email=email,
                phone=phone,
                message=message
            )
            messages.success(request, "Your message has been sent successfully.")
        else:
            messages.error(request, "Please fill in all required fields.")

        return redirect('contactUs')
    context = {
        "header": header,
        'locations': locations,
        'faqs': faqs
    }
    return render(request, 'front/pages/contact-us.html',context)


def shop(request):
    return render(request, 'front/shop/shop.html')


def productDetails(request):
    return render(request, 'front/shop/product-details.html')





def vendor_list(request):
    return render(request, 'front/vendor/vendor-store-list.html')

def single_vendor(request):
    return render(request, 'front/vendor/vendor-store-single.html')

def become_a_vendor(request):
    header = vendorregisterPageHeader.objects.filter(is_active=True).first()
    context={
        "header":header,
    }
    return render(request, 'front/vendor/become-a-vendor.html',context)

def blog_list(request):
    header=BlogListPageHeader.objects.filter(is_active=True).first()
    context={
        "header":header,
    }
    return render(request, 'front/blog/blog-list.html',context)

def post_single(request):
    header=BlogPageHeader.objects.filter(is_active=True).first()
    context={
        "header":header,
    }
    return render(request, 'front/blog/blog-single.html',context)



def error404(request):
    return render(request, 'front/pages/error-404.html')

def faq(request):
    return render(request, 'front/pages/faq.html')

def myAccount(request):
    return render(request, 'front/profile/my-account.html')

def wishlist(request):
    return render(request, 'front/shop/wishlist.html')

def compare(request):
    return render(request, 'front/shop/compare.html')

def add_To_cart(request):
    return render(request, 'front/order/Addcart.html')

def checkOut(request):
    return render(request, 'front/order/checkout.html')

def orderComplete(request):
    return render(request, 'front/order/orderComplete.html')