from django.shortcuts import render, redirect
from django.contrib import messages
from smart.models import *
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import reverse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate, login,logout
from django.db import transaction
from django.conf import settings
from django.contrib.auth import get_user_model
import datetime






User = get_user_model()


def home(request):
    sliders = Slider.objects.all().order_by('position')
    brands = list(ClientBrand.objects.all())
    banners = CategoryBanner.objects.all()
    ad_banners= AdvertisingBanner.objects.all()
    
    # Group images in pairs
    brand_pairs = [brands[i:i+2] for i in range(0, len(brands), 2)]
    
    context = {
        'sliders': sliders,
        'brand_pairs': brand_pairs,
        'banners': banners,
        'ad_banners': ad_banners
    }
    return render(request, 'front/index.html', context)


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


#login--

def login_user(request):
    if request.method == "POST":
        username = request.POST.get("login_email")
        password = request.POST.get("login_password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # send back the URL for the home page
            return JsonResponse({
                "message": "Login successful.",
                "redirect_url": reverse("home")
            })
        else:
            return JsonResponse({"message": "Invalid credentials."}, status=400)
    return render(request, 'front/pages/login.html')


# @require_POST
# def login_view(request):
#     username = request.POST.get("login_email")
#     password = request.POST.get("login_password")

#     user = authenticate(request, username=username, password=password)
#     if user is not None:
#         login(request, user)
#         # send back the URL for the home page
#         return JsonResponse({
#             "message": "Login successful.",
#             "redirect_url": reverse("home")
#         })
#     else:
#         return JsonResponse({"message": "Invalid credentials."}, status=400)


@require_POST
def user_signup(request):
    data = request.POST
    errors = {}

    # Required fields
    required_fields = ["first-name", "phone", "password", "confirm-password", "terms"]
    for field in required_fields:
        if not data.get(field):
            errors[field] = ["This field is required."]

    # Password match
    if data.get("password") != data.get("confirm-password"):
        errors["confirm-password"] = ["Passwords do not match."]

    # Validate password strength
    # try:
    #     validate_password(data.get("password"))
    # except ValidationError as ve:
    #     errors["password"] = ve.messages
    
    if data.get("password") and len(data.get("password")) < 6:
        errors["password"] = ["Password must be at least 6 characters long."]
    
    

    # Unique check only if email is provided
    email = data.get("email", "").strip()
    if email and User.objects.filter(email=email).exists():
        errors["email"] = ["Email already exists."]

    # Unique phone number check
    if User.objects.filter(phone_number=data.get("phone")).exists():
        errors["phone"] = ["Phone number already exists."]

    if errors:
        # Extract the first error message to show globally
        first_error_message = next(iter(errors.values()))[0]
        return JsonResponse({
            "errors": errors,
            "message": first_error_message  # show this in `showMessage("error", ...)`
        }, status=400)

    # Create the user
    user = User.objects.create_user(
        email=email if email else None,
        username=email if email else data.get("phone"),  # fallback username
        phone_number=data.get("phone"),
        first_name=data.get("first-name"),
        last_name=data.get("last-name") or None,
        password=data.get("password"),
        user_type=3,  # client
        user_status=1  # active
    )

    return JsonResponse({
        "message": "Account created successfully. Redirecting to login..."
    }, status=201)


from django.contrib.auth.decorators import login_required
@login_required
def update_account_details(request):
    user = request.user

    if request.method == 'POST':
        print("POST:", request.POST)

        # Basic info
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        display_name = request.POST.get('display_name')
        email = request.POST.get('email_1')

        if firstname:
            user.first_name = firstname
        if lastname:
            user.last_name = lastname
        if display_name:
            user.username = display_name
        if email and email != user.email:
            if User.objects.filter(email=email).exclude(id=user.id).exists():
                messages.error(request, "Email already in use.")
                return redirect("myAccount")
            user.email = email

        # Unique phone number
        phone_number = request.POST.get('phone_number')
        if phone_number and phone_number != user.phone_number:
            if User.objects.filter(phone_number=phone_number).exclude(id=user.id).exists():
                messages.error(request, "Phone number already in use.")
                return redirect("myAccount")
            user.phone_number = phone_number

        # Other optional fields
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        postal_code = request.POST.get('postal_code')

        if address:
            user.address = address
        if city:
            user.city = city
        if state:
            user.state = state
        if postal_code:
            user.postal_code = postal_code

        # Password change
        cur_password = request.POST.get('cur_password')
        new_password = request.POST.get('new_password')
        conf_password = request.POST.get('conf_password')

        if cur_password or new_password or conf_password:
            if not cur_password or not new_password or not conf_password:
                messages.error(request, "Please fill all password fields.")
                return redirect("myAccount")

            if not user.check_password(cur_password):
                messages.error(request, "Current password is incorrect.")
                return redirect("myAccount")

            if new_password != conf_password:
                messages.error(request, "New passwords do not match.")
                return redirect("myAccount")

            user.set_password(new_password)
            login(request, user)  # Re-authenticate

        # Finally, save the user
        user.save()
        messages.success(request, "Account details updated successfully.")
        return redirect("myAccount")

    return redirect("myAccount")


def logout_user(request):
    logout(request)
    return redirect('login_user')


def become_a_vendor(request):
    header = vendorregisterPageHeader.objects.filter(is_active=True).first()
    packages = Package.objects.all().order_by('package_id')
    
    context={
        "header":header,
        'packages': packages
    }
    return render(request, 'front/vendor/become-a-vendor.html',context)


@require_POST
def save_vendor(request):
    if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

    try:
        with transaction.atomic():
            data = request.POST
            files = request.FILES
            
            # Get or create user
            if request.user.is_authenticated:
                user = request.user
            else:
                # For non-logged-in users
                email = data.get('email')
                if not email:
                    return JsonResponse({'success': False, 'message': 'Email is required'})
                
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        'first_name': data.get('full_name', '').split(' ')[0],
                        'last_name': ' '.join(data.get('full_name', '').split(' ')[1:]),
                        'phone_number': data.get('phone'),
                        'address': data.get('address'),
                        'city': data.get('city'),
                        'postal_code': data.get('postal_code'),
                        'is_active': False
                    }
                )

            # Update user info
            full_name = data.get('full_name', '').strip()
            first_name, last_name = (full_name.split(' ', 1) if ' ' in full_name else (full_name, ''))

            user.first_name = first_name
            user.last_name = last_name
            user.email = data.get('email')
            user.phone_number = data.get('phone')
            user.address = data.get('address')
            user.city = data.get('city')
            user.postal_code = data.get('postal_code')
            user.package_id = data.get('package')
            user.save()

            # Create/update vendor contact info
            VendorContactInfo.objects.update_or_create(
                user=user,
                defaults={
                    'business_logo': files.get('logo'),
                    'business_name': data.get('business_name'),
                    'business_address': data.get('business_address'),
                    'phone_number': data.get('business_phone'),
                    'business_email': data.get('business_email'),
                    'contact_person_name': data.get('contact_person_name'),
                    'contact_person_phone': data.get('contact_person_phone'),
                }
            )

            # Create/update company overview
            VendorCompanyOverview.objects.update_or_create(
                user=user,
                defaults={
                    'business_details': data.get('business_details'),
                    'tax_certificate': files.get('tax_certificate'),
                    'trade_licence': files.get('trade_licence'),
                    'establishment_date': datetime.datetime.strptime(data.get('established_date'), "%Y-%m-%d").date() if data.get('established_date') else None,
                    'business_type': data.get('business_type'),
                    'is_licensed': data.get('licensed') == "Yes",
                    'is_insured': data.get('insured') == "Yes",
                    'additional_info': data.get('additional_info'),
                }
            )

            # Create/update financial info
            VendorFinancialInfo.objects.update_or_create(
                user=user,
                defaults={
                    'bank_name': data.get('bank_name'),
                    'card_last4': (data.get('card_number') or '')[-4:],
                    'expiration_date': '07/2030',  # Placeholder
                    'shift_code': 'SHIFT-CODE',    # Placeholder
                }
            )
            
            # Create verification record
            VendorVerification.objects.get_or_create(user=user)

            return JsonResponse({
                'success': True, 
                'message': 'Vendor application submitted successfully! Our team will review your information shortly.'
            })

    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'An error occurred: {str(e)}'
        }, status=500)




































def shop(request):
    return render(request, 'front/shop/shop.html')


def productDetails(request):
    return render(request, 'front/shop/product-details.html')





def vendor_list(request):
    return render(request, 'front/vendor/vendor-store-list.html')

def single_vendor(request):
    return render(request, 'front/vendor/vendor-store-single.html')


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
    header=FaqsPageHeader.objects.filter(is_active=True).first()
    context={
        "header":header,
        }
    return render(request, 'front/pages/faq.html',context)

def myAccount(request):
    return render(request, 'front/profile/my-account.html')

def wishlist(request):
    header=WishlistPageHeader.objects.filter(is_active=True).first()
    context={
        "header":header,
        }
    return render(request, 'front/shop/wishlist.html',context)

def compare(request):
    return render(request, 'front/shop/compare.html')

def add_To_cart(request):
    return render(request, 'front/order/Addcart.html')

def checkOut(request):
    return render(request, 'front/order/checkout.html')

def orderComplete(request):
    return render(request, 'front/order/orderComplete.html')





#login--
def userlogin(request):
    return render(request,'front/pages/login.html')