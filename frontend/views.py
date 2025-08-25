from django.shortcuts import render, redirect
from django.contrib import messages
from smart.models import *
from smart.forms import *
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
import traceback
from django.views.decorators.http import require_POST
from django.db.models import Avg, Count
from django.shortcuts import reverse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate, login,logout
from django.db import transaction
from django.conf import settings
from django.contrib.auth import get_user_model
from itertools import chain
import datetime
import random
import string
from .utils.utils import get_discounted_price, get_new_arrivals






User = get_user_model()

def home(request):
    sliders       = Slider.objects.all().order_by('position')
    brands        = list(ClientBrand.objects.all())
    brand_pairs   = [brands[i:i+2] for i in range(0, len(brands), 2)]
    banners       = CategoryBanner.objects.all()
    ad_banners    = AdvertisingBanner.objects.all()
    offer_banners = OfferBanner.objects.all()
    product_list  = Product.objects.all()

    # new arrivals
    new_arrivals  = get_new_arrivals(limit=10)
    # Attach slides to ad banners
    attach_products_to_ad_banners(ad_banners)

    return render(request, 'front/index.html', {
        'sliders': sliders,
        'brand_pairs': brand_pairs,
        'banners': banners,
        'ad_banners': ad_banners,
        'offer_banners': offer_banners,
        'product': product_list,
        'new_arrivals': new_arrivals,
    })
    
    
    
def attach_products_to_ad_banners(ad_banners):
    for banner in ad_banners:
        # Get up to 2 categories from the banner
        categories = list(banner.categories.all())[:2]
        product_chunks = []

        for category in categories:
            products = (Product.objects
                        .filter(category=category, publish_status=1)
                        .order_by('?')[:4])
            product_chunks.append(list(products))  # keep separate per category

        # Merge all products into one list (8 total)
        all_products = list(chain.from_iterable(product_chunks))

        # Split into slides of 2 products each
        banner.slides = [all_products[i:i+2] for i in range(0, len(all_products), 2)]

        # Debug print (optional)
        print(f"AdvertisingBanner {banner.id} — Categories: {[c.name for c in categories]}")
        print(f"Fetched products: {[p.title for p in all_products]}")
        


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
        

def product_details(request, slug):
    product = get_object_or_404(Product, slug=slug)
    images = product.images.all().order_by('position')
    
    # Get the first discount for this product
    discount = product.discounts.first()
    
    # Calculate final price
    final_price = product.selling_price
    if discount:
        if discount.discount_type == 'fixed':
            final_price = product.selling_price - discount.discount_price
        elif discount.discount_type == 'percentage':
            # Convert percentage value (like 500 = 5%, 1000 = 10%)
            discount_percent = discount.percentage / 1000
            final_price = product.selling_price - (product.selling_price * discount_percent)
            
    # Get related products (same category, exclude current)
    related_products = Product.objects.filter(
        category=product.category  # Same category as current product
    ).exclude(id=product.id).order_by('?')[:6]  # Random 6 products from same category
    
    # Split into chunks of 3 for swiper slides
    related_chunks = [list(related_products)[i:i+3] for i in range(0, len(related_products), 3)]
    
   # Reviews handling - modified to work without custom filters
    reviews = product.reviews.all().order_by('-created_at')
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    total_reviews = reviews.count()
    
    # Calculate rating distribution as a dictionary
    rating_distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for review in reviews:
        rating_distribution[review.rating] += 1
    
    # Calculate percentages and prepare data for template
    rating_data = []
    for rating in [5, 4, 3, 2, 1]:
        count = rating_distribution[rating]
        percentage = (count / total_reviews * 100) if total_reviews > 0 else 0
        rating_data.append({
            'rating': rating,
            'count': count,
            'percentage': round(percentage, 1)
        })
    
    # Calculate recommended percentage (4-5 stars)
    recommended_count = reviews.filter(rating__gte=4).count()
    recommended_percentage = (recommended_count / total_reviews * 100) if total_reviews > 0 else 0
    
    # Review form handling (keep your existing code)
    if request.method == 'POST' and request.POST.get('review_submit') == '1':
        review_form = ProductReviewForm(request.POST)
        if review_form.is_valid():
            new_review = review_form.save(commit=False)
            new_review.product = product
            new_review.save()
            return redirect('product_details', slug=product.slug)
    else:
        review_form = ProductReviewForm()
    
    context = {
        'product': product,
        'images': images,
        'discount': discount,
        'final_price': final_price,
        'related_products': related_chunks,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'total_reviews': total_reviews,
        'rating_data': rating_data,
        'recommended_count': recommended_count,
        'recommended_percentage': round(recommended_percentage, 1),
        'review_form': review_form,
    }
    return render(request, 'front/shop/product_details.html', context)



def cart(request):

    return render(request, 'front/order/cart.html')


def add_to_cart(request):
    if request.method == "POST":
        product_id = str(request.POST.get("product_id"))
        quantity = int(request.POST.get("quantity", 1))
        product = get_object_or_404(Product, pk=product_id)

        now = timezone.now()
        original_price = product.selling_price  # Decimal
        discount_amount = Decimal("0.00")

        discounts = product.discounts.filter(active=True).filter(
            (Q(start_date__lte=now) | Q(start_date__isnull=True)) &
            (Q(end_date__gte=now) | Q(end_date__isnull=True))
        )

        if discounts.exists():
            discount = discounts.first()
            if discount.discount_type == ProductDiscount.FIXED and discount.discount_price is not None:
                discount_amount = discount.discount_price
            elif discount.discount_type == ProductDiscount.PERCENT and discount.percentage is not None:
                discount_amount = original_price * (discount.percentage / Decimal("100"))
            elif discount.discount_type == ProductDiscount.BULK:
                if discount.bulk_quantity and quantity >= discount.bulk_quantity:
                    if discount.bulk_discount_type == ProductDiscount.FIXED and discount.bulk_discount_value:
                        discount_amount = discount.bulk_discount_value
                    elif discount.bulk_discount_type == ProductDiscount.PERCENT and discount.bulk_discount_value:
                        discount_amount = original_price * (discount.bulk_discount_value / Decimal("100"))
            elif discount.discount_type == ProductDiscount.BOGO:
                pass  # Implement if needed

        final_price = max(original_price - discount_amount, Decimal("0.00"))

        cart = request.session.get("cart", {})

        if product_id in cart:
            cart[product_id]["quantity"] += quantity
            # Optionally update price & discount for existing items too:
            cart[product_id]["price"] = str(final_price.quantize(Decimal("0.01")))
            cart[product_id]["discount"] = str(discount_amount.quantize(Decimal("0.01")))
        else:
            cart[product_id] = {
                "title": product.title,
                "price": str(final_price.quantize(Decimal("0.01"))),
                "discount": str(discount_amount.quantize(Decimal("0.01"))),
                "quantity": quantity,
                "thumbnail": product.thumbnail_image.url if product.thumbnail_image else "",
            }

        request.session["cart"] = cart
        request.session.modified = True
        
        subtotal = sum(Decimal(item["price"]) * item["quantity"] + Decimal(item["discount"]) * item["quantity"] for item in cart.values())
        discount_total = sum(Decimal(item["discount"]) * item["quantity"] for item in cart.values())
        grand_total = subtotal - discount_total

        # return JsonResponse({
        #     "status": "success",
        #     "message": f"{product.title} added to cart",
        #     "cart_count": sum(item["quantity"] for item in cart.values())
        # })
        
        return JsonResponse({
            "status": "success",
            "message": f"{product.title} added to cart",
            "cart_count": sum(item["quantity"] for item in cart.values()),
            "product": {
                "id": product.id,
                "slug": product.slug,
                "title": product.title,
                "price": str(final_price.quantize(Decimal("0.01"))),
                "quantity": cart[product_id]["quantity"],
                "image": product.thumbnail_image.url if product.thumbnail_image else "",
            },
            "subtotal": str(subtotal.quantize(Decimal("0.01"))),
            "discount_total": str(discount_total.quantize(Decimal("0.01"))),
            "grand_total": str(grand_total.quantize(Decimal("0.01"))),
        })

    return JsonResponse({"status": "error", "message": "Invalid request"})

 
@require_POST
def update_quantity(request):
    item_id = request.POST.get('id')
    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            quantity = 1
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid quantity'}, status=400)

    cart = request.session.get('cart', {})

    if item_id not in cart:
        return JsonResponse({'success': False, 'error': 'Item not found'}, status=404)

    product = get_object_or_404(Product, pk=item_id)
    now = timezone.now()
    original_price = product.selling_price  # Decimal
    discount_amount = Decimal('0.00')

    discounts = product.discounts.filter(active=True).filter(
        (Q(start_date__lte=now) | Q(start_date__isnull=True)) &
        (Q(end_date__gte=now) | Q(end_date__isnull=True))
    )

    if discounts.exists():
        discount = discounts.first()
        if discount.discount_type == ProductDiscount.FIXED and discount.discount_price is not None:
            discount_amount = discount.discount_price
        elif discount.discount_type == ProductDiscount.PERCENT and discount.percentage is not None:
            discount_amount = original_price * (discount.percentage / Decimal('100'))
        elif discount.discount_type == ProductDiscount.BULK:
            if discount.bulk_quantity and quantity >= discount.bulk_quantity:
                if discount.bulk_discount_type == ProductDiscount.FIXED and discount.bulk_discount_value:
                    discount_amount = discount.bulk_discount_value
                elif discount.bulk_discount_type == ProductDiscount.PERCENT and discount.bulk_discount_value:
                    discount_amount = original_price * (discount.bulk_discount_value / Decimal('100'))
        elif discount.discount_type == ProductDiscount.BOGO:
            pass  # Implement if needed

    final_price = max(original_price - discount_amount, Decimal('0.00'))

    cart[item_id]['quantity'] = quantity
    cart[item_id]['price'] = str(final_price.quantize(Decimal('0.01')))
    cart[item_id]['discount'] = str(discount_amount.quantize(Decimal('0.01')))
    request.session['cart'] = cart
    request.session.modified = True

    total_items = sum(int(i.get('quantity', 0)) for i in cart.values())
    subtotal = sum(Decimal(i.get('price', '0')) * int(i.get('quantity', 0)) for i in cart.values())
    item_subtotal = final_price * quantity

    return JsonResponse({
        'success': True,
        'cart_count': total_items,
        'subtotal': float(subtotal),
        'item_subtotal': float(item_subtotal),
    })


@require_POST
def remove_item(request):
    item_id = request.POST.get('id')
    cart = request.session.get('cart', {})
    if item_id in cart:
        del cart[item_id]
    request.session['cart'] = cart
    request.session.modified = True

    total_items = sum(int(i.get('quantity', 0)) for i in cart.values())
    subtotal = sum(float(i.get('price', 0)) * int(i.get('quantity', 0)) for i in cart.values())

    return JsonResponse({
        'success': True,
        'cart_count': total_items,
        'subtotal': subtotal,
    })


@require_POST
def clear_cart(request):
    request.session['cart'] = {}
    request.session.modified = True
    return JsonResponse({
        'success': True,
        'cart_count': 0,
        'subtotal': 0,
    })
    
    
def create_shipping_address(data):
    # Assuming your Address model fields, adjust as needed
    return Address.objects.create(
        email=data.get("email"),
        phone=data.get("phone"),
        firstname=data.get("firstname"),
        lastname=data.get("lastname"),
        street_address_1=data.get("street_address_1"),
        street_address_2=data.get("street_address_2"),
        town=data.get("town"),
        zip_code=data.get("zip"),
    )

def create_order(user, cart_items, subtotal, discount_total, shipping_total, grand_total, shipping_address):
    order = Order.objects.create(
        order_number="ORD-" + str(uuid4())[:8].upper(),
        customer=user,
        payment_method=0,  # Cash on Delivery
        subtotal=subtotal,
        discount_total=discount_total,
        shipping_total=shipping_total,
        grand_total=grand_total,
        shipping_address=shipping_address,
    )
    # TODO: create OrderVendor and OrderItem instances here if you want
    return order

    
def order_checkout(request):
    cart_data = cart_context(request)
    shipping_cost = Decimal("100.00")  # fixed shipping cost, or calculate dynamically

    context = {
        "cart_items": cart_data["cart_items"],
        "total_price_without_discount": cart_data["subtotal"],
        "cart_discount_total": cart_data["discount_total"],
        "shipping_cost": shipping_cost,
        "cart_total": (cart_data["grand_total"] + shipping_cost).quantize(Decimal("0.01")),
    }

    return render(request, 'front/order/checkout.html', context)


@require_POST
def place_order(request):
    try:
        user = request.user if request.user.is_authenticated else None
        
        print('************************hit *****************')

        # Get form data
        phone = request.POST.get('phone', '').strip()
        firstname = request.POST.get('firstname', '').strip()
        lastname = request.POST.get('lastname', '').strip()
        street_address_1 = request.POST.get('street-address-1', '').strip()
        city = request.POST.get('city', '').strip()
        street_address_2 = request.POST.get('street-address-2', '').strip()
        town = request.POST.get('town', '').strip()
        zip_code = request.POST.get('zip', '').strip()

        # Validate required fields (phone, street_address_1, etc)
        # if not phone:
        #     return render(request, 'front/order/checkout.html', {'error': 'Phone number is required.'})
        # if not street_address_1:
        #     return render(request, 'front/order/checkout.html', {'error': 'Street address is required.'})
        # # You can add more validation here if needed

        # Compose full street address
        full_street_address = street_address_1
        if street_address_2:
            full_street_address += ", " + street_address_2

        # For now, skipping district and thana - set None
        district = None
        thana = None

        print('saving adresss*****************************************')
        # Create Address
        address = Address.objects.create(
            user=user,
            title="Home",
            district=district,  # Requires district FK nullable in model
            thana=thana,        # Requires thana FK nullable in model
            street_address=full_street_address,
            postal_code=zip_code or None,
            phone_number=phone,
            city=city,
            is_default=True,
        )

        cart = request.session.get("cart", {})
        if not cart:
            return redirect('cart')

        subtotal = Decimal('0.00')
        discount_total = Decimal('0.00')
        shipping_total = Decimal("100.00")  # Hardcoded shipping cost

        # Create the Order
        order = Order.objects.create(
            customer=user,  # None for guest
            subtotal=Decimal('0.00'),
            discount_total=Decimal('0.00'),
            shipping_total=shipping_total,
            grand_total=Decimal('0.00'),
            shipping_address=address,
            billing_address=address,
        )

        # Process cart items
        for product_id, item in cart.items():
            product = Product.objects.get(pk=product_id)
            quantity = item.get('quantity', 1)

            price = product.selling_price
            discount = (
                product.discounts.filter(active=True)
                .filter(start_date__lte=timezone.now(), end_date__gte=timezone.now())
                .first()
            )

            if discount:
                if discount.discount_type == ProductDiscount.FIXED and discount.discount_price:
                    discounted_price = discount.discount_price
                elif discount.discount_type == ProductDiscount.PERCENT and discount.percentage:
                    discounted_price = price * (Decimal("1") - discount.percentage / Decimal("100"))
                else:
                    discounted_price = price
            else:
                discounted_price = price

            base_price = price
            discount_amount = base_price - discounted_price
            final_price = discounted_price

            vendor = product.seller

            vendor_order, created = OrderVendor.objects.get_or_create(
                order=order,
                vendor=vendor,
                defaults={
                    'vendor_subtotal': Decimal('0.00'),
                    'vendor_discount': Decimal('0.00'),
                    'vendor_total': Decimal('0.00'),
                }
            )
            
            print('saving order -----------------------------------')

            OrderItem.objects.create(
                vendor_order=vendor_order,
                product=product,
                quantity=quantity,
                base_price=base_price,
                discount_amount=discount_amount,
                final_price=final_price,
                discount_applied=discount,
            )

            vendor_order.vendor_subtotal += base_price * quantity
            vendor_order.vendor_discount += discount_amount * quantity
            vendor_order.vendor_total += final_price * quantity
            vendor_order.save()

            subtotal += base_price * quantity
            discount_total += discount_amount * quantity

        grand_total = subtotal - discount_total + shipping_total

        order.subtotal = subtotal
        order.discount_total = discount_total
        order.shipping_total = shipping_total
        order.grand_total = grand_total
        order.save()

        # Clear cart after order saved
        request.session['clear_cart_after_success'] = True


        return redirect('order_success')

    except Exception as e:
        error_message = f"An error occurred: {str(e)}\n\n{traceback.format_exc()}"
        print(error_message)
        return render(request, 'front/order/checkout.html', {'error': error_message})
    
    
from .context_processors import cart_context

def order_success(request):
    if request.user.is_authenticated:
        order = Order.objects.filter(customer=request.user).order_by('-created_at').first()
    else:
        order = Order.objects.order_by('-created_at').first()

    if not order:
        return redirect('home')

    cart_data = cart_context(request)
    
    shipping_cost = 100

    context = {
        'order': order,
        'cart_items': cart_data['cart_items'],
        'total_price_without_discount': cart_data['subtotal'],
        'cart_discount_total': cart_data['discount_total'],
        'shipping_cost': shipping_cost,     
        'grand_total': cart_data['grand_total'] + shipping_cost, 
    }

    # Render the page
    response = render(request, 'front/order/order_success.html', context)

    # Clear cart after page is generated
    if request.session.get('clear_cart_after_success'):
        request.session['cart'] = {}
        del request.session['clear_cart_after_success']

    return response


    

 
def product_quickview(request, product_id):
    product = get_object_or_404(Product, pk=product_id, publish_status=1)

    # Prepare images (thumbnail first, then gallery images)
    images = []
    if product.thumbnail_image:
        images.append(request.build_absolute_uri(product.thumbnail_image.url))
    gallery_images = [request.build_absolute_uri(img.image.url) for img in product.images.all()]
    images.extend(gallery_images)

    # Calculate price and discount
    final_price, discount_value, discount_type = get_discounted_price(product)

    data = {
        'id': product.id,
        'title': product.title,
        'price': str(final_price),
        'old_price': str(product.selling_price) if discount_value else None,
        'discount_value': str(discount_value) if discount_value else None,
        'discount_type': discount_type,
        'description': product.description or "",
        'sku': product.sku,
        'category': product.category.name if product.category else None,
        'images': images,
    }
    return JsonResponse(data)

@login_required
def create_customer_product(request):
    # ===== New: enforce upload limit before processing =====
    vendor_verification = VendorVerification.objects.filter(user=request.user).first()
    vendor_status = vendor_verification.status if vendor_verification else '0'
    product_count = Product.objects.filter(seller=request.user).count()

    if request.user.user_type == 0:
        return JsonResponse({
            'success': False,
            'error': "Your account type isn't allowed to upload products."
        }, status=403)

    if request.user.user_type == 3 or (request.user.user_type == 1 and vendor_status in ['0', '2']):
        if product_count >= 2:
            return JsonResponse({
                'success': False,
                'error': "Update your package  — your 2-product limit is finished."
            }, status=403)
    # ========================================================

    if request.method == 'POST':
        try:
            # Validate required fields
            required_fields = ['sku', 'title', 'selling_price', 'stock_quantity']
            for field in required_fields:
                if not request.POST.get(field):
                    return JsonResponse({
                        'success': False,
                        'error': f"Missing required field: {field}"
                    }, status=400)

            # Handle main product data
            product = Product(
                seller=request.user,
                sku=request.POST.get('sku'),
                title=request.POST.get('title'),
                description=request.POST.get('description', ''),
                selling_price=Decimal(request.POST.get('selling_price', 0)),
                buy_price=Decimal(request.POST.get('initial_price', 0)),
                stock_quantity=int(request.POST.get('stock_quantity', 0)),
                stock_availability=request.POST.get('stock_status', 'In stock') == 'In stock',
                low_stock_level=int(request.POST.get('low_stock_level', 5)),
                is_digital_product=request.POST.get('is_digital') == 'on',
                meta_title=request.POST.get('meta_title', ''),
                meta_keywords=request.POST.get('meta_keywords', ''),
                meta_description=request.POST.get('meta_description', ''),
                weight=Decimal(request.POST.get('weight', 0)),
                length=Decimal(request.POST.get('length', 0)),
                width=Decimal(request.POST.get('width', 0)),
                height=Decimal(request.POST.get('height', 0)),
                publish_status=int(request.POST.get('publish_status', 0)),
            )

            # Generate unique slug
            product.slug = slugify(product.title)
            while Product.objects.filter(slug=product.slug).exists():
                rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
                product.slug = f"{slugify(product.title)}-{rand_str}"

            # Handle thumbnail image
            if 'thumbnail' in request.FILES:
                product.thumbnail_image = request.FILES['thumbnail']

            product.save()

            # Handle categories
            category_ids = request.POST.getlist('categories[]')
            try:
                if category_ids:
                    product.category = Category.objects.get(id=category_ids[0])
                    if len(category_ids) > 1:
                        product.sub_category = Category.objects.get(id=category_ids[1])
                    if len(category_ids) > 2:
                        product.sub_sub_category = Category.objects.get(id=category_ids[2])
                    product.save()
            except Category.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': "Invalid category selected"
                }, status=400)

            # Handle gallery images
            if 'gallery[]' in request.FILES:
                for i, image in enumerate(request.FILES.getlist('gallery[]')):
                    ProductImage.objects.create(
                        product=product,
                        image=image,
                        position=i
                    )

            # Handle discounts
            if request.POST.get('fixed_discount'):
                ProductDiscount.objects.create(
                    product=product,
                    discount_type='fixed',
                    discount_price=Decimal(request.POST.get('fixed_discount')),
                )
            elif request.POST.get('percentage_discount'):
                ProductDiscount.objects.create(
                    product=product,
                    discount_type='percentage',
                    percentage=Decimal(request.POST.get('percentage_discount')),
                )

            return JsonResponse({
                'success': True, 
                'message': 'Product added successfully',
                'product_id': product.id
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    # GET request - show form
    categories = Category.objects.filter(parent_category__isnull=True)
    context = {
        'categories': categories,
        "breadcrumb": {
            "title": "Add Product",
            "parent": "ECommerce", 
            "child": "Add Product"
        }
    }
    return render(request, 'front/products/create_customer_product.html', context)





































from django.db.models import Min, Max

from django.core.paginator import Paginator

def shop(request):
    products = Product.objects.filter(publish_status=1)

    # --- price filter + sorting logic (from before) ---
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    if min_price and max_price:
        products = products.filter(selling_price__gte=min_price, selling_price__lte=max_price)
    elif min_price:
        products = products.filter(selling_price__gte=min_price)
    elif max_price:
        products = products.filter(selling_price__lte=max_price)

    orderby = request.GET.get("orderby", "default")
    if orderby == "price-low":
        products = products.order_by("selling_price")
    elif orderby == "price-high":
        products = products.order_by("-selling_price")
    elif orderby == "date":
        products = products.order_by("-created_at")
    else:
        products = products.order_by("-created_at")

    count = int(request.GET.get("count", 12))
    paginator = Paginator(products, count)
    page_number = request.GET.get("page")
    products_page = paginator.get_page(page_number)

    categories = Category.objects.filter(status=1, parent_category__isnull=True)

    # Default banner
    banner_url = '/static/front/assets/images/shop/banner1.jpg'

    return render(request, "front/shop/shop.html", {
        "products": products_page,
        "categories": categories,
        "orderby": orderby,
        "count": count,
        "banner_url": banner_url
    })



def shop_by_category(request, slug):
    category = get_object_or_404(Category, slug=slug, status=1)
    products = Product.objects.filter(publish_status=1, category=category)
    categories = Category.objects.filter(status=1).exclude(parent_category=None)

    # Check if category has a banner
    banner_url = category.banner.url if category.banner else None

    return render(request, 'front/shop/shop.html', {
        'products': products,
        'categories': categories,
        'selected_category': category,
        'banner_url': banner_url
    })



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

@login_required
def myAccount(request):
    # Get orders for the current user
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    
    # Get products uploaded by the current user (using seller field)
    products = Product.objects.filter(seller=request.user).order_by('-created_at')
    
    # ===== New: determine if the user can upload more products =====
    vendor_verification = VendorVerification.objects.filter(user=request.user).first()
    vendor_status = vendor_verification.status if vendor_verification else '0'
    product_count = products.count()

    if request.user.user_type == 0:
        can_upload = False
    elif request.user.user_type == 3 or (request.user.user_type == 1 and vendor_status in ['0', '2']):
        can_upload = product_count < 2
    else:
        can_upload = True

    context = {
        'orders': orders,
        'products': products,
        'can_upload': can_upload,  # pass to template for "Add Products" link visibility
    }
    return render(request, 'front/profile/my-account.html', context)


def wishlist(request):
    header=WishlistPageHeader.objects.filter(is_active=True).first()
    context={
        "header":header,
        }
    return render(request, 'front/shop/wishlist.html',context)

def compare(request):
    return render(request, 'front/shop/compare.html')


def orderComplete(request):
    return render(request, 'front/order/orderComplete.html')





#login--
def userlogin(request):
    return render(request,'front/pages/login.html')