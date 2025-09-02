from django.shortcuts import render,redirect
from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.core.validators import validate_email
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.utils.html import strip_tags
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.db import IntegrityError
from django.contrib.auth import login,logout,authenticate
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .forms import *
import traceback
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST
import datetime
import string
import random
import json
import os
import re
from .models import *




def is_valid_email(email):
    """Simple regex for email validation"""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)


@login_required(login_url="/admin-dashboard/login_home")
def dashboard(request):
    print('my user---------------------------------: ', request.user)
    context = {
        "breadcrumb":{
            "title":"E-Commerce",
            "parent":"Dashboard",
            "child":"E-Commerce"
        },
    }
    
    return render(request, "general/dashboard/dashboard-02.html", context)


@login_required(login_url="/admin-dashboard/login_home")
def index(request):
    sliders = Slider.objects.all().order_by('position')
    context = {
        "breadcrumb":{
            "title":"Default","parent":"Dashboard","child":"Default"
        },
    }
    return render(request,'index.html', context)


def signup_home(request):
    if request.method == "GET":
        return render(request, 'sign-up.html')
    else:
        email = request.POST['email']
        username = request.POST['username']
        password = request.POST['password']
        user = User.objects.filter(email=email).exists()
        if user:
            raise Exception('Something went wrong')
        new_user = User.objects.create_user(username=username,email=email, password=password).exis
        new_user.save()
        return redirect('index')
    
    
def logout_view(request):
    logout(request)
    return redirect('login_home')


def login_home(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password  = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            print('login user:', user)
            if user is not None:
                login(request,user)
                if 'next' in request.GET:
                    nextPage = request.GET['next']
                    return HttpResponseRedirect(nextPage)
                return redirect("dashboard")
            else:
                messages.error(request,"Wrong credentials")
                return redirect("login_home")
        else:
            messages.error(request,"Wrong credentials")
            return redirect("login_home")
    else:
        form = AuthenticationForm()        
        
    return render(request,'login.html',{"form":form,})



def add_slider(request):
    name = request.POST.get('name')
    status = request.POST.get('status')
    button_link = request.POST.get('button_link')
    text_alignment = request.POST.get('text_alignment') or 0
    paragraph = request.POST.get('paragraph')
    paragraph_color = request.POST.get('paragraph_color')
    heading_h3 = request.POST.get('heading_h3')
    heading_h3_color = request.POST.get('heading_h5_color')
    heading_h5 = request.POST.get('heading_h5')
    heading_h5_color = request.POST.get('heading_h5_color')
    background_image = request.FILES.get('background_image')
    
    print('heading_h3: ', heading_h3)
    print('heading_h3_color: ', heading_h3_color)
    print('heading_h5: ', heading_h5)
    print('heading_h5_color: ', heading_h5_color)

    if not name or not background_image:
        return JsonResponse({'status': 'error', 'message': 'Name and background image are required.'})

    try:
        Slider.objects.create(
            name=name,
            status=status,
            button_link=button_link,
            text_alignment=text_alignment,
            paragraph=paragraph,
            paragraph_color=paragraph_color,
            heading_h3=heading_h3,
            heading_h3_color=heading_h3_color,
            heading_h5=heading_h5,
            heading_h5_color=heading_h5_color,
            background_image=background_image,
        )
        return JsonResponse({'status': 'success', 'message': 'Slider added successfully.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error: {str(e)}'})
    
    
def update_slider(request):
    # --- Start Debugging: Print all request data ---
    print("--- Request Data Start ---")
    print(f"Request Method: {request.method}")
    print("GET Parameters:", request.GET)
    print("POST Parameters:")
    for key, value in request.POST.items():
        print(f"  {key}: {value}")
    print("FILES (Uploaded Files):")
    for key, file in request.FILES.items():
        print(f"  {key}: {file.name} ({file.size} bytes)")
    print("--- Request Data End ---")
    # --- End Debugging ---
    
    
    slider_id = request.POST.get("slider_id")
    if not slider_id:
        return JsonResponse({"status": "error", "message": "Missing slider ID."})

    slider = get_object_or_404(Slider, id=slider_id)

    # Update fields
    slider.name = request.POST.get("name")
    slider.paragraph = request.POST.get("paragraph")
    slider.paragraph_color = request.POST.get("paragraph_color")
    slider.heading_h3 = request.POST.get("heading_h3")
    slider.heading_h3_color = request.POST.get("heading_h3_color")
    slider.heading_h5 = request.POST.get("heading_h5")
    slider.heading_h5_color = request.POST.get("heading_h5_color")
    slider.button_link = request.POST.get("button_link")
    slider.status = request.POST.get("status")
    slider.position = request.POST.get("edit_position")
    slider.text_alignment = request.POST.get("text_alignment")

    # Handle image replacements
    if "image" in request.FILES:
        if slider.image:
            if os.path.isfile(slider.image.path):
                os.remove(slider.image.path)
        slider.image = request.FILES["image"]

    if "background_image" in request.FILES:
        if slider.background_image:
            if os.path.isfile(slider.background_image.path):
                os.remove(slider.background_image.path)
        slider.background_image = request.FILES["background_image"]

    try:
        slider.save()
    except IntegrityError as e:
        # You can either return the raw message...
        return JsonResponse(
            {"status": "error", "message": str(e)},
            status=400
        )
    return JsonResponse({"status": "success", "message": "Slider updated successfully."})
    



def sliders(request):
    if request.method == "POST":
        method_override = request.POST.get("_method", "").upper()

        if method_override == "PUT":
            return update_slider(request)
        elif request.POST.get("name") and request.FILES.get("background_image"):
            return add_slider(request)

    else:
        alignment_choices = Slider.ALIGNMENT_CHOICES 
        sliders = Slider.objects.all()
        
        context = {
            'sliders': sliders,
            'alignment_choices': alignment_choices,
        }
        return render(request, 'home_content/sliders/sliders.html', context)



def regions(request):
    if request.method == 'POST':
        # data = json.loads(request.body.decode('utf-8'))
        # action = data.get('action')

        # if action == 'add':
        #     name = data.get('name')
        #     url = data.get('url')
            
        #     print('name to add: ', name)
        #     print('url to add: ', url)
            
        #     if not name or not url:
        #         return JsonResponse({'status': 'error', 'message': 'All fields are required.'})
        #     Region.objects.create(name=name, url=url)
            return JsonResponse({'status': 'success', 'message': 'Region added successfully.'})

        # elif action == 'edit':
        #     region_id = data.get('id')
        #     name = data.get('name')
        #     url = data.get('url')
        #     if not region_id or not name or not url:
        #         return JsonResponse({'status': 'error', 'message': 'All fields are required.'})
        #     try:
        #         region = Region.objects.get(id=region_id)
        #         region.name = name
        #         region.url = url
        #         region.save()
        #         return JsonResponse({'status': 'success', 'message': 'Region updated successfully.'})
        #     except Region.DoesNotExist:
        #         return JsonResponse({'status': 'error', 'message': 'Region not found.'})

        # elif action == 'delete':
        #     region_id = data.get('id')
        #     try:
        #         Region.objects.get(id=region_id).delete()
        #         return JsonResponse({'status': 'success', 'message': 'Region deleted successfully.'})
        #     except Region.DoesNotExist:
        #         return JsonResponse({'status': 'error', 'message': 'Region not found.'})

    else:
        # regions = Region.objects.all()
        
        context = {
            # 'regions': regions,
        }
        return render(request, 'regions/regions.html', context)



@login_required(login_url="/admin-dashboard/login_home")
def user_accounts(request):
    # user_accounts = UserAccount.objects.all()
    # regions = Region.objects.all()
    
    context = {
        # 'user_accounts': user_accounts,
        # 'regions': regions,
    }
    
    return render(request, 'user_accounts/user_accounts.html', context)


def add_user_account(request):
    if request.method == 'POST':
        # email = request.POST.get('email')
        # password = request.POST.get('password')
        # region_id = request.POST.get('region')
        # key = request.POST.get('key')
        # name = request.POST.get('name')
        # phone = request.POST.get('phone')

        # # Validate required fields
        # if not email or not password or not key or not region_id:
        #     return JsonResponse({'success': False, 'status': 'error', 'message': 'All required fields must be filled.'}, status=400)

        # # Validate email format
        # try:
        #     validate_email(email)
        # except ValidationError:
        #     return JsonResponse({'success': False, 'status': 'error', 'message': 'Invalid email format.'}, status=400)

        # # Check for existing email
        # if UserAccount.objects.filter(email=email).exists():
        #     return JsonResponse({'success': False, 'status': 'error', 'message': 'Email already exists.'}, status=400)

        # # Validate region
        # try:
        #     region = Region.objects.get(id=region_id)
        # except Region.DoesNotExist:
        #     return JsonResponse({'success': False, 'status': 'error', 'message': 'Selected region is invalid.'}, status=400)

        # # Save user
        # user = UserAccount.objects.create(
        #     name=name,
        #     email=email,
        #     user_password=password,
        #     auth_key=key,
        #     phone=phone,
        #     region=region
        # )
        
        return JsonResponse({'success': True, 'status': 'success', 'message': 'User account created successfully.'})

    # For GET or other methods, render the form page
    # regions = Region.objects.all()
    context = {
        'regions': regions
    }
    return render(request, 'user_accounts/add_user_account.html', context)



@login_required(login_url="/admin-dashboard/login_home")
def user_list(request):
    users = User.objects.all()
    
    context = {
        'users': users,
    }
    
    return render(request, 'users/user_list.html', context)



def add_user(request):
    if request.method == 'POST':
        email        = request.POST.get('email', '').strip()
        password     = request.POST.get('password', '').strip()
        username     = request.POST.get('username', '').strip()
        first_name     = request.POST.get('first_name', '').strip()
        last_name     = request.POST.get('last_name', '').strip()
        phone        = request.POST.get('phone', '').strip()
        address      = request.POST.get('address', '').strip()
        city         = request.POST.get('city', '').strip()
        state        = request.POST.get('state', '').strip()
        postal_code  = request.POST.get('postal_code', '').strip()

        # 1) Required‐field validation
        if not email or not password:
            return JsonResponse({
                'success': False,
                'status': 'error',
                'message': 'Email, password and package selection are required.'
            }, status=400)

        # 2) Email format
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({
                'success': False,
                'status': 'error',
                'message': 'Invalid email format.'
            }, status=400)

        # 3) Unique constraints
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'status': 'error',
                'message': 'Email already exists.'
            }, status=400)
        if username and User.objects.filter(username=username).exists():
            return JsonResponse({
                'success': False,
                'status': 'error',
                'message': 'Username already exists.'
            }, status=400)
        if phone and User.objects.filter(phone_number=phone).exists():
            return JsonResponse({
                'success': False,
                'status': 'error',
                'message': 'Phone number already exists.'
            }, status=400)

        # 5) Create user
        user = User(
            email=email,
            username=username or None,
            phone_number=phone or None,
            first_name=first_name or '',
            last_name=last_name or '',
            address=address or None,
            city=city or None,
            state=state or None,
            postal_code=postal_code or None,
        )
        
        user.set_password(password)
        user.save()
        
        print('User created successfully----------------------------------------------:', user)

        return JsonResponse({
            'success': True,
            'status': 'success',
            'message': 'User account created successfully.'
        })

    # GET → render form
    packages = Package.objects.all().order_by('package_id')
    return render(request, 'users/add_user.html', {
        'packages': packages
    })
    

@login_required(login_url="/admin-dashboard/login_home")
def edit_user_account(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'status': 'error', 'message': 'Invalid method.'}, status=405)

    user_id = request.POST.get('id')
    if not user_id:
        return JsonResponse({'success': False, 'status': 'error', 'message': 'Missing user ID.'}, status=400)

    user = get_object_or_404(User, pk=user_id)

    # Pull fields from form
    email       = request.POST.get('email', '').strip()
    password    = request.POST.get('password', '').strip()
    username    = request.POST.get('username', '').strip()
    first_name  = request.POST.get('first_name', '').strip()
    last_name   = request.POST.get('last_name', '').strip()
    phone       = request.POST.get('phone', '').strip()
    address     = request.POST.get('address', '').strip()
    city        = request.POST.get('city', '').strip()
    state       = request.POST.get('state', '').strip()
    postal_code = request.POST.get('postal_code', '').strip()

    # 1) Required: email only
    if not email:
        return JsonResponse({
            'success': False,
            'status': 'error',
            'message': 'Email is required.'
        }, status=400)

    # 2) Email format
    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({
            'success': False,
            'status': 'error',
            'message': 'Invalid email format.'
        }, status=400)

    # 3) Email uniqueness (exclude self)
    if User.objects.exclude(pk=user.pk).filter(email=email).exists():
        return JsonResponse({
            'success': False,
            'status': 'error',
            'message': 'Email already in use by another account.'
        }, status=400)

    # 4) Username uniqueness (exclude self)
    if username and User.objects.exclude(pk=user.pk).filter(username=username).exists():
        return JsonResponse({
            'success': False,
            'status': 'error',
            'message': 'Username already in use.'
        }, status=400)

    # 5) Phone uniqueness (exclude self)
    if phone and User.objects.exclude(pk=user.pk).filter(phone_number=phone).exists():
        return JsonResponse({
            'success': False,
            'status': 'error',
            'message': 'Phone number already in use.'
        }, status=400)

    # All clear—apply updates
    user.email        = email
    user.username     = username or None
    user.first_name   = first_name or ''
    user.last_name    = last_name or ''
    user.phone_number = phone or None
    user.address      = address or None
    user.city         = city or None
    user.state        = state or None
    user.postal_code  = postal_code or None

    if password:
        user.set_password(password)

    user.save()

    return JsonResponse({
        'success': True,
        'status': 'success',
        'message': 'User updated successfully.'
    })


def delete_user_account(request):
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            user_id = data.get('id')
            
            if not user_id:
                return JsonResponse({'success': False, 'message': 'User ID is required.'}, status=400)
            
            # Get the user object
            user = get_object_or_404(User, pk=user_id)
            
            # Delete the user
            user.delete()
            
            return JsonResponse({'success': True, 'message': 'User account deleted successfully.'})
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON data.'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error deleting user: {str(e)}'}, status=500)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)



from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Product, Category

@login_required(login_url="/admin-dashboard/login_home")
def list_products(request):
    products = Product.objects.filter(seller=request.user)
    categories = Category.objects.all()
    
    context = {
        "products": products,
        "categories": categories,
        "breadcrumb": {
            "title": "Product List",
            "parent": "Ecommerce", 
            "child": "Product List"
        }
    }
    return render(request, 'products/product_list.html', context)
    
    
@login_required(login_url="/admin-dashboard/login_home")
def pending_products(request):
    products = Product.objects.pending()
    categories = Category.objects.all()
    
    product_request = True
    
    context = {
        "products": products,
        "categories": categories,
        'product_request': product_request,
        "breadcrumb": {
            "title": "Product List",
            "parent": "Ecommerce", 
            "child": "Product List"
        }
    }
    return render(request, 'products/product_list.html', context)



def update_product_from_request(product, request):
    """Helper function to update a product instance from request data."""
    # Update basic fields
    product.sku = request.POST.get('sku')
    product.title = request.POST.get('title')
    product.description = request.POST.get('description')

    # Categories
    category_id = request.POST.get('category')
    if category_id:
        product.category = Category.objects.get(id=category_id)

    sub_category_id = request.POST.get('sub_category')
    if sub_category_id:
        product.sub_category = Category.objects.get(id=sub_category_id)

    sub_sub_category_id = request.POST.get('sub_sub_category')
    if sub_sub_category_id:
        product.sub_sub_category = Category.objects.get(id=sub_sub_category_id)

    # Pricing
    product.initial_price = request.POST.get('initial_price', 0) or 0
    product.selling_price = request.POST.get('selling_price', 0) or 0

    # Shipping
    product.weight = request.POST.get('weight', 0) or 0
    product.length = request.POST.get('length', 0) or 0
    product.width = request.POST.get('width', 0) or 0
    product.height = request.POST.get('height', 0) or 0

    # SEO
    product.meta_title = request.POST.get('meta_title')
    product.meta_keywords = request.POST.get('meta_keywords')
    product.meta_description = request.POST.get('meta_description')

    # Status (⚠️ You probably want publish_status, not status)
    product.publish_status = request.POST.get('publish_status', Product.DRAFT)

    # Thumbnail
    if 'thumbnail' in request.FILES:
        product.thumbnail_image = request.FILES['thumbnail']

    # Gallery
    if 'gallery[]' in request.FILES:
        product.images.all().delete()
        for image in request.FILES.getlist('gallery[]'):
            ProductImage.objects.create(product=product, image=image)

    # Save product
    product.save()

    # Tags
    tag_list = json.loads(request.POST.get('tags', '[]'))
    for tag_obj in tag_list:
        tag_name = tag_obj.get('value')
        if tag_name:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            product.tags.add(tag)

    return product



@login_required(login_url="/admin-dashboard/login_home")
def edit_product(request, id):
    product = get_object_or_404(Product, id=id)
    categories = Category.objects.all()

    if request.method == 'POST':
        try:
            update_product_from_request(product, request)
            return JsonResponse({'success': True, 'message': 'Product updated successfully!'})
        except Exception as e:
            print(traceback.format_exc())
            return JsonResponse({'success': False, 'message': str(e), 'errors': {'server_error': [str(e)]}})
        
    context = {
        "product": product,
        "categories": categories,
        "breadcrumb": {"title": "Edit Product", "parent": "Ecommerce", "child": "Edit Product"}
    }

    return render(request, 'products/edit_products.html', context)


@login_required(login_url="/admin-dashboard/login_home")
def single_product_request(request, id):
    product = get_object_or_404(Product, id=id)
    categories = Category.objects.all()

    if request.method == 'POST':
        try:
            update_product_from_request(product, request)
            return JsonResponse({'success': True, 'message': 'Product updated successfully!'})
        except Exception as e:
            print(traceback.format_exc())
            return JsonResponse({'success': False, 'message': str(e), 'errors': {'server_error': [str(e)]}})
        
    context = {
        "product": product,
        "categories": categories,
        "breadcrumb": {"title": "Edit Product", "parent": "Ecommerce", "child": "Edit Product"}
    }

    return render(request, 'products/single_product_request.html', context)


def delete_product(request):
    if request.method == 'DELETE':
        # try:
        #     data = json.loads(request.body.decode('utf-8'))
        #     print('delete data: ', data)
        #     product_id = int(data.get('id'))
        # except (ValueError, TypeError, json.JSONDecodeError):
        #     return JsonResponse({'success': False, 'message': 'Invalid data'}, status=400)

        # try:
        #     product = Product.objects.get(id=product_id)
        # except Product.DoesNotExist:
        #     return JsonResponse({'success': False, 'message': 'User account not found.'}, status=404)

        # product.delete()
        return JsonResponse({'success': True, 'message': 'User account deleted successfully.'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)


#--------------------------new add product--------


def create_product(request):
    if request.method != "POST":
        return JsonResponse({'success': False, 'errors': {'request': 'Invalid request method'}})

    data = request.POST
    files = request.FILES
    
    print('data for product saving: ', data)

    try:
        errors = {}

        # Required fields
        sku = data.get('sku')
        title = data.get('title')
        selling_price = data.get('selling_price')
        category_id = data.get('category')

        if not sku:
            errors['sku'] = "SKU is required."
        if not title:
            errors['title'] = "Title is required."
        if not selling_price:
            errors['selling_price'] = "Selling price is required."
        if not category_id:
            errors['category'] = "Category is required."

        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        description = data.get('description', '')
        model = data.get('model', '')
        short_description = data.get('short_description', '')
        
        print('********model about to be save*********: ', model)
        print('********short_description about to be save*********: ', short_description)
        
        thumbnail = files.get('thumbnail') if 'thumbnail' in files else None
        gallery_files = files.getlist('gallery[]')

        sub_category_id = data.get('sub_category') or None
        sub_sub_category_id = data.get('sub_sub_category') or None

        meta_title = data.get('meta_title')
        meta_keywords = data.get('meta_keywords')
        meta_description = data.get('meta_description')

        shipping_class_name = data.get('shipping_class')
        shipping_class = ShippingClass.objects.filter(name=shipping_class_name).first() if shipping_class_name else None

        publish_status = data.get('publish_status') or 1
        publish_date = parse_datetime(data.get('publish_date')) if data.get('publish_date') else None
        
        if 'thumbnail' in files:
            thumbnail = files['thumbnail']
            # further details:
            print("Thumbnail name:", thumbnail.name)
            print("Thumbnail size:", thumbnail.size)
            print("Thumbnail content-type:", thumbnail.content_type)
        else:
            thumbnail = None
            print("No thumbnail received from frontend")

        
        
        if sub_sub_category_id:
            main_category_id = sub_sub_category_id
        elif sub_category_id:
            main_category_id = sub_category_id
        else:
            main_category_id = category_id

        # Create product
        product = Product.objects.create(
            sku=sku,
            title=title,
            model=model,
            short_description=short_description,
            description=description,
            thumbnail_image=thumbnail,
            selling_price=selling_price,
            category_id=main_category_id,
            parent_category_id=category_id,
            sub_category_id=sub_category_id,
            sub_sub_category_id=sub_sub_category_id,
            meta_title=meta_title,
            meta_keywords=meta_keywords,
            meta_description=meta_description,
            shipping_class=shipping_class,
            publish_date=publish_date,
            seller=request.user  # replace or mock this as needed
        )

        # Tags (JSON list of objects)
        tag_list = json.loads(data.get('tags', '[]'))
        for tag_obj in tag_list:
            tag_name = tag_obj.get('value')
            if tag_name:
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                product.tags.add(tag)

        # Save gallery images
        for i, image in enumerate(gallery_files):
            if image:
                ProductImage.objects.create(product=product, image=image, position=i)

        # Discount
        discount_type = data.get('discount_Type')
        if discount_type == 'Fixed Price':
            fixed_price = data.get('fixed_discount')
            if fixed_price:
                ProductDiscount.objects.create(
                    product=product,
                    discount_type='fixed',
                    discount_price=fixed_price,
                    active=True
                )
        elif discount_type == 'Percentage':
            percentage = data.get('discount_percentage')
            if percentage:
                ProductDiscount.objects.create(
                    product=product,
                    discount_type='percentage',
                    percentage=percentage,
                    active=True
                )

        return JsonResponse({'success': True, 'message': "Product created successfully!"})

    except Exception as e:
        print("Exception occurred:", str(e))
        print(traceback.format_exc())  # <-- This prints the full traceback in terminal
        return JsonResponse({'success': False, 'errors': {'exception': str(e)}}, status=500)







def update_contact_header(request):
    header = contactPageHeader.objects.first()  # Only 1 entry expected
    if request.method == 'POST':
        title = request.POST.get('title')
        is_active = request.POST.get('is_active') == 'on'
        image = request.FILES.get('background_image')

        if not header:
            header = contactPageHeader()

        header.title = title
        header.is_active = is_active
        if image:
            header.background_image = image
        header.save()
        return redirect('update_contact_header')

    return render(request, 'applications/contacts/page-header.html', {'header': header})



@login_required(login_url="/admin-dashboard/login_home")
def contacts(request):
    
    faqs = contactFAQ.objects.all().order_by('order')

    if request.method == 'POST':
        form = contactFAQorm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('contacts')  # ensure this name matches your urls.py
    else:
        form = contactFAQorm()

    context = {
        "breadcrumb": {
            "title": "Contacts",
            "parent": "Apps",
            "child": "Contacts"
        },
        
        "faqs": faqs,
        "form": form
    }
    return render(request, "applications/contacts/contacts.html", context)

@login_required(login_url="/admin-dashboard/login_home")
def update_contactfaq(request, pk):
    faq = get_object_or_404(contactFAQ, pk=pk)
    if request.method == 'POST':
        form = contactFAQorm(request.POST, instance=faq)
        if form.is_valid():
            form.save()
    return redirect('contacts')

@login_required(login_url="/admin-dashboard/login_home")
def delete_contactfaq(request, pk):
    faq = get_object_or_404(contactFAQ, pk=pk)
    faq.delete()
    return redirect('contacts')


#---contact us form msg
@login_required(login_url="/admin-dashboard/login_home")
def delete_contactfaq(request, pk):
    faq = get_object_or_404(contactFAQ, pk=pk)
    faq.delete()
    return redirect('contacts')



#user messages--
@login_required(login_url="/admin-dashboard/login_home")
def contact_messages(request):
    messages_list = ContactMessage.objects.all().order_by('-created_at')
    context = {
        "breadcrumb": {"title": "Contact Messages", "parent": "Apps", "child": "Messages"},
        "messages": messages_list
    }
    return render(request, "applications/contacts/message.html", context)

@login_required(login_url="/admin-dashboard/login_home")
def delete_contact_message(request, pk):
    if request.method == "POST":
        message = get_object_or_404(ContactMessage, pk=pk)
        message.delete()
        messages.success(request, "Message deleted successfully.")
    return redirect('contact_messages')

@login_required
def contactUs_location(request):
    locations = ContactLocation.objects.all()

    # Handle AJAX POST requests for add/edit/delete
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        action = request.POST.get('action')

        if action == "add":
            form = ContactLocationForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                return JsonResponse({"success": True, "message": "Location added successfully."})
            else:
                return JsonResponse({"success": False, "errors": form.errors})

        elif action == "edit":
            loc_id = request.POST.get('id')
            location = get_object_or_404(ContactLocation, id=loc_id)
            form = ContactLocationForm(request.POST, request.FILES, instance=location)
            if form.is_valid():
                form.save()
                return JsonResponse({"success": True, "message": "Location updated successfully."})
            else:
                return JsonResponse({"success": False, "errors": form.errors})

        elif action == "delete":
            loc_id = request.POST.get('id')
            location = get_object_or_404(ContactLocation, id=loc_id)
            location.delete()
            return JsonResponse({"success": True, "message": "Location deleted successfully."})

        else:
            return JsonResponse({"success": False, "message": "Invalid action."})

    # GET request - just render page
    return render(request, 'applications/contacts/contactLocations.html', {"locations": locations})


#-----------------become a vendor
#page header
def update_vendor_header(request):
    header = vendorregisterPageHeader.objects.first()  # Only 1 entry expected
    if request.method == 'POST':
        title = request.POST.get('title')
        is_active = request.POST.get('is_active') == 'on'
        image = request.FILES.get('background_image')

        if not header:
            header = vendorregisterPageHeader()

        header.title = title
        header.is_active = is_active
        if image:
            header.background_image = image
        header.save()
        return redirect('update_vendor_header')

    return render(request, 'applications/ecommerce/seller/vendorheader.html', {'header': header})


#-----------------blog List ---
#page header
def blogList_header(request):
    header = BlogListPageHeader.objects.first()  # Only 1 entry expected
    if request.method == 'POST':
        title = request.POST.get('title')
        is_active = request.POST.get('is_active') == 'on'
        image = request.FILES.get('background_image')

        if not header:
            header = BlogListPageHeader()

        header.title = title
        header.is_active = is_active
        if image:
            header.background_image = image
        header.save()
        return redirect('blogList_header')

    return render(request, 'miscellaneous/blog/blogList-header.html', {'header': header})



#-----------------blog single ---
#page header
def blog_header(request):
    header = BlogPageHeader.objects.first()  # Only 1 entry expected
    if request.method == 'POST':
        title = request.POST.get('title')
        is_active = request.POST.get('is_active') == 'on'
        image = request.FILES.get('background_image')

        if not header:
            header = BlogPageHeader()

        header.title = title
        header.is_active = is_active
        if image:
            header.background_image = image
        header.save()
        return redirect('blog_header')

    return render(request, 'miscellaneous/blog/blog-header.html', {'header': header})


#-----------aboutUS header

def aboutUs_header(request):
    header = AboutusPageHeader.objects.first()  # Only 1 entry expected
    if request.method == 'POST':
        title = request.POST.get('title')
        is_active = request.POST.get('is_active') == 'on'
        image = request.FILES.get('background_image')

        if not header:
            header = AboutusPageHeader()

        header.title = title
        header.is_active = is_active
        if image:
            header.background_image = image
        header.save()
        return redirect('aboutUs_header')

    return render(request, 'aboutus/aboutus-header.html', {'header': header})

def aboutus_content(request):
    if request.method == "POST":
        content_id = request.POST.get("id")
        if content_id:  # Edit
            content = get_object_or_404(AboutPageContent, pk=content_id)
        else:  # Add new
            content = AboutPageContent()

        content.title = request.POST.get("title")
        content.description = request.POST.get("description")
        content.button_text = request.POST.get("button_text")
        content.button_url = request.POST.get("button_url")

        if request.FILES.get("image"):
            content.image = request.FILES["image"]
            # Resize image to 610x450
            img = Image.open(content.image)
            img = img.resize((610, 450), Image.LANCZOS)
            img.save(content.image.path)

        content.save()
        return redirect("aboutus_content")

    contents = AboutPageContent.objects.all()
    return render(request, "aboutus/aboutus-content.html", {"contents": contents})


def delete_about_page_content(request, pk):
    content = get_object_or_404(AboutPageContent, pk=pk)
    content.delete()
    return redirect("aboutus_content")


#-----------faq header

def faqs_header(request):
    header = FaqsPageHeader.objects.first()  # Only 1 entry expected
    if request.method == 'POST':
        title = request.POST.get('title')
        is_active = request.POST.get('is_active') == 'on'
        image = request.FILES.get('background_image')

        if not header:
            header = FaqsPageHeader()

        header.title = title
        header.is_active = is_active
        if image:
            header.background_image = image
        header.save()
        return redirect('faqs_header')

    return render(request, 'applications/faqs/faqs-header.html', {'header': header})


#-----------wishlist header

def wishlist_header(request):
    header = WishlistPageHeader.objects.first()  # Only 1 entry expected
    if request.method == 'POST':
        title = request.POST.get('title')
        is_active = request.POST.get('is_active') == 'on'
        image = request.FILES.get('background_image')

        if not header:
            header = WishlistPageHeader()

        header.title = title
        header.is_active = is_active
        if image:
            header.background_image = image
        header.save()
        return redirect('wishlist_header')

    return render(request, 'applications/wishlist/wishlist-header.html', {'header': header})


@login_required(login_url="/admin-dashboard/login_home")
def add_products(request):
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
                    
            
            print('*******************************short description: ', request.POST.get('short_description', ''))
            print('*******************************product model: ', request.POST.get('short_description', ''))
            # Handle main product data
            product = Product(
                seller=request.user,
                sku=request.POST.get('sku'),
                title=request.POST.get('title'),
                model=request.POST.get('model', ''),
                description=request.POST.get('description', ''),
                short_description=request.POST.get('short_description', ''),
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
            print('================1=================',product)

            # Generate unique slug
            product.slug = slugify(product.title)
            while Product.objects.filter(slug=product.slug).exists():
                rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
                product.slug = f"{slugify(product.title)}-{rand_str}"

            # Handle thumbnail image
            if 'thumbnail' in request.FILES:
                product.thumbnail_image = request.FILES['thumbnail']

            product.save()
            print('===============2==================',product)

            

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
            discount_value = None
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
    return render(request, "products/add_products.html", context)


@login_required(login_url="/admin-dashboard/login_home")
def product_details(request):
    context = { "breadcrumb":{"title":"Product Details","parent":"Ecommerce", "child":"Product Details"}}
    return render(request,"products/product_details.html",context)


def product_review(request):
    review=ProductReview.objects.all()
    context={
        'review':review,
    }
    return render (request,'products/product_review.html',context) 


#---------------Ecommerce-------------------#

@login_required(login_url="/admin-dashboard/login_home")
def product_grid(request):
    context = { "breadcrumb":{"title":"Product Grid","parent":"Ecommerce", "child":"Product Grid"}}
    return render(request,"applications/ecommerce/products/product-grid.html",context)


def get_subcategories(request, parent_id):
    subcategories = Category.objects.filter(parent_category_id=parent_id).values('id', 'name')
    return JsonResponse(list(subcategories), safe=False)

def get_user_data(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        print('user data: ', user)
        return JsonResponse({
            'email': user.email,
            'phone_number': user.phone_number,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'address': user.address,
            'city': user.city,
            'state': user.state,
            'postal_code': user.postal_code,
        })
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)



def vendor_list(request):
    packages = Package.objects.all().order_by('package_id')
    users = User.objects.filter(user_type=3).order_by('username')  # customers
    context = {
        'packages': packages,
        'users': users,
        
        "breadcrumb":{
            "title":"Vendor List",
            "parent":"Ecommerce",
            "child":"Vendor List"
        },
    }
    return render(request, "vendors/vendor_list.html", context)


def vendors(request):
    # Fetch all users who are vendors
    user_type_list = [1, 3]
    # vendors = User.objects.filter(user_type=1).select_related(
    #     'contact_info', 'vendorverification'
    # )
    
    vendors = User.objects.filter(user_type__in=user_type_list).select_related(
        'contact_info', 'vendorverification'
    )

    return render(request, 'vendors/vendors.html', {
        'vendors': vendors
    })



def add_vendor(request):
    packages = Package.objects.all().order_by('package_id')
    users = User.objects.filter(user_type=3).order_by('username')  # customers
    context = {
        'packages': packages,
        'users': users,
        
        "breadcrumb":{
            "title":"Add Vendor",
            "parent":"Vendors",
            "child":"Add Vendor",
        },
    }
    return render(request, "vendors/add_vendor.html", context)


@require_POST
def save_vendor(request):
    if not request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

    try:
        with transaction.atomic():
            data = request.POST
            files = request.FILES
            
            print('data: ', data)
            
            user_id = int(data.get('user'))

            user = get_object_or_404(User, id=user_id)

            # === 1. Update Personal Info ===
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
            user.is_active = True
            user.save()

            # === 2. Contact Info ===
            VendorContactInfo.objects.update_or_create(
                user=user,
                defaults={
                    'business_logo': files.get('logo'),
                    'business_name': data.get('business_name'),
                    'business_address': data.get('business_address'),
                    'phone_number': data.get('business_phone'),
                    'postal_code': data.get('postal_code'),
                    'business_email': data.get('business_email'),
                    'contact_person_name': data.get('contact_person_name'),
                    'contact_person_phone': data.get('contact_person_phone'),
                }
            )

            # === 3. Company Overview ===
            VendorCompanyOverview.objects.update_or_create(
                user=user,
                defaults={
                    'business_details': data.get('business_details'),
                    'tax_certificate': files.get('tax_certificate'),
                    'trade_licence': files.get('trade_licence'),
                    'establishment_date': datetime.datetime.strptime(data.get('established_date'), "%Y-%m-%d").date() if data.get('established_date') else None,
                    'business_type': data.get('business_type'),
                    'is_licensed': (data.get('licensed') == "Yes"),
                    'is_insured': (data.get('insured') == "Yes"),
                    'additional_info': data.get('additional_info'),
                }
            )

            # === 4. Financial Info ===
            VendorFinancialInfo.objects.update_or_create(
                user=user,
                defaults={
                    'bank_name': data.get('bank_name'),
                    'card_last4': (data.get('card_number') or '')[-4:],
                    'expiration_date': '07/2030',  # Placeholder
                    'shift_code': 'SHIFT-CODE',    # Replace with logic
                }
            )
            
            VendorVerification.objects.get_or_create(user=user)

            return JsonResponse({'success': True, 'status': 'success', 'message': 'Vendor profile updated successfully!'})

    except Exception as e:
        print(f"Error saving vendor: {e}")
        return JsonResponse({'success': False, 'status': 'error', 'message': f'Error: {str(e)}'})
    
    
def vendor(request, id):
    vendor = get_object_or_404(
        User.objects.select_related(
            'contact_info',
            'company_overview',
            'financial_info',
            'vendorverification',
        ), id=id
    )
    
    print('vendor: ', vendor)
    return render(request, 'vendors/vendor.html', {'vendor': vendor})


@require_POST
def update_vendor(request, id):
    if request.method != "POST" or request.headers.get("X-Requested-With") != "XMLHttpRequest":
        return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=400)

    user = get_object_or_404(User, id=id)

    contact_info, _ = VendorContactInfo.objects.get_or_create(user=user)
    company_info, _ = VendorCompanyOverview.objects.get_or_create(user=user)
    financial_info, _ = VendorFinancialInfo.objects.get_or_create(user=user)
    verification, _ = VendorVerification.objects.get_or_create(user=user)

    # === CONTACT INFO ===
    contact_info.business_name = request.POST.get("business_name")
    contact_info.business_email = request.POST.get("business_email")
    contact_info.business_address = request.POST.get("business_address")
    contact_info.contact_person_name = request.POST.get("contact_person_name")
    contact_info.contact_person_phone = request.POST.get("contact_person_phone")
    contact_info.save()

    # === COMPANY OVERVIEW ===
    company_info.business_details = request.POST.get("business_details")
    company_info.establishment_date = request.POST.get("establishment_date")
    company_info.business_type = request.POST.get("business_type")
    company_info.is_licensed = bool(int(request.POST.get("is_licensed", 0)))
    company_info.is_insured = bool(int(request.POST.get("is_insured", 0)))

    if request.FILES.get("tax_certificate"):
        company_info.tax_certificate = request.FILES["tax_certificate"]

    if request.FILES.get("trade_licence"):
        company_info.trade_licence = request.FILES["trade_licence"]

    company_info.save()

    # === FINANCIAL INFO ===
    financial_info.bank_name = request.POST.get("bank_name")
    financial_info.card_last4 = request.POST.get("card_last4")
    financial_info.expiration_date = request.POST.get("expiration_date")
    financial_info.shift_code = request.POST.get("shift_code")
    financial_info.save()

    # === VERIFICATION ===
    verification.status = int(request.POST.get("verification_status"))
    verification.rejection_reason = request.POST.get("rejection_reason")
    verification.save()
    
    print('verification.status: ', verification.status)
    
    # === UPDATE USER TYPE BASED ON VERIFICATION ===
    if verification.status == 1:  # Approved
        user.user_type = 1  # Vendor
    else:
        print('else part printed')
        user.user_type = 3  # Client
        
    user.save(update_fields=["user_type"])
    
    print('user_type: ', user.user_type)

    return JsonResponse({
        "success": True,
        "status": "success",
        "message": "Vendor profile updated successfully."
    })



def packages(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        action = data.get('action')

        if action == 'add':
            name = data.get('name')
            description = data.get('description')
            max_products = data.get('max_products', 0)
            can_use_variants = data.get('can_use_variants', False)
            can_create_discounts = data.get('can_create_discounts', False)
            price = data.get('price', 0.0)
            duration_days = data.get('duration_days', 30)
            
            package_type = int(data.get('package_type', 0))

            if not name:
                return JsonResponse({'status': 'error', 'message': 'Package name is required.'})

            Package.objects.create(
                name=name,
                description=description,
                max_products=max_products,
                can_use_variants=can_use_variants,
                can_create_discounts=can_create_discounts,
                price=price,
                duration_days=duration_days,
                package_type=package_type
            )
            return JsonResponse({'status': 'success', 'message': 'Package added successfully.'})
        
        elif action == 'edit':
            package_id = data.get('id')
            name = data.get('name')
            description = data.get('description')
            max_products = data.get('max_products', 0)
            can_use_variants = data.get('can_use_variants', False)
            can_create_discounts = data.get('can_create_discounts', False)
            price = data.get('price', 0.0)
            duration_days = data.get('duration_days', 30)
            package_type = int(data.get('package_type', 0))

            if not package_id or not name:
                return JsonResponse({'status': 'error', 'message': 'Missing required fields.'})

            try:
                package = Package.objects.get(id=package_id)
                package.name = name
                package.description = description
                package.max_products = max_products
                package.can_use_variants = can_use_variants
                package.can_create_discounts = can_create_discounts
                package.price = price
                package.duration_days = duration_days
                package.package_type = package_type
                package.save()
                return JsonResponse({'status': 'success', 'message': 'Package updated successfully.'})
            except Package.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Package not found.'})

        elif action == 'delete':
            package_id = data.get('id')
            
            if not package_id:
                return JsonResponse({'status': 'error', 'message': 'Package ID is required.'})

            try:
                package = Package.objects.get(id=package_id)
                package.delete()
                return JsonResponse({'status': 'success', 'message': 'Package deleted successfully.'})
            except Package.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Package not found.'})

    else:
        packages = Package.objects.all().order_by('package_id')
        context = {
            'packages': packages,
            'package_type_choices': Package.PACKAGE_TYPE_CHOICES,
            
            "breadcrumb":{
                "title":"Packages",
                "parent":"Ecommerce",
                "child":"Packages"
            },
        }
        return render(request, 'packages/packages.html', context)


@login_required(login_url="/admin-dashboard/login_home")
def category_type(request):
    if request.method == "GET":
        category_types = CategoryType.objects.all()
        return render(request, "category/categoryType.html", {'category_types': category_types})
    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            action = data.get("action")

            if action == "add":
                name = data.get("name")
                if not name:
                    return JsonResponse({"status": "error", "message": "Name is required."})
                
                if CategoryType.objects.filter(name=name).exists():
                    return JsonResponse({"status": "error", "message": "Category type already exists."})

                CategoryType.objects.create(name=name)
                return JsonResponse({"status": "success", "message": "Category type added successfully."})

            elif action == "edit":
                cat_id = data.get("id")
                name = data.get("name")
                if not name or not cat_id:
                    return JsonResponse({"status": "error", "message": "ID and Name are required."})

                try:
                    category = CategoryType.objects.get(id=cat_id)
                    category.name = name
                    category.slug = ""  # Reset slug to regenerate if needed
                    category.save()
                    return JsonResponse({"status": "success", "message": "Category type updated successfully."})
                except CategoryType.DoesNotExist:
                    return JsonResponse({"status": "error", "message": "Category type not found."})

            elif action == "delete":
                cat_id = data.get("id")
                if not cat_id:
                    return JsonResponse({"status": "error", "message": "ID is required for deletion."})
                try:
                    category = CategoryType.objects.get(id=cat_id)
                    category.delete()
                    return JsonResponse({"status": "success", "message": "Category type deleted successfully."})
                except CategoryType.DoesNotExist:
                    return JsonResponse({"status": "error", "message": "Category type not found."})

            else:
                return JsonResponse({"status": "error", "message": "Invalid action."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Error: {str(e)}"})

    return JsonResponse({"status": "error", "message": "Invalid request method."})


@login_required(login_url="/admin-dashboard/login_home")
def category(request):
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Handle AJAX requests
        if action == 'get_category':
            slug = request.POST.get('slug')
            try:
                category = get_object_or_404(Category, slug=slug)
                data = {
                    'id': category.id,
                    'slug': category.slug,
                    'name': category.name,
                    'parent_category': category.parent_category.id if category.parent_category else '',
                    'category_type': category.category_type.id if category.category_type else '',
                    'status': str(category.status),
                    'description': category.description or '',
                    'meta_title': category.meta_title or '',
                    'meta_key': category.meta_key or '',
                    'meta_description': category.meta_description or '',
                    # Add image URLs
                    'banner': category.banner.url if category.banner else '',
                    'thumbnail_small': category.thumbnail_small.url if category.thumbnail_small else '',
                    'icon': category.icon.url if category.icon else '',
                }
                return JsonResponse({'success': True, 'data': data})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        elif action == 'update_category':
            original_slug = request.POST.get('original_slug')
            try:
                category = get_object_or_404(Category, slug=original_slug)
                
                # Extract form data
                name = request.POST.get('name')
                new_slug = request.POST.get('slug')
                parent_id = request.POST.get('parent_category')
                category_type_id = request.POST.get('category_type')
                status = request.POST.get('status')
                description = request.POST.get('description')
                meta_title = request.POST.get('meta_title')
                meta_key = request.POST.get('meta_key')
                meta_description = request.POST.get('meta_description')

                # Get related objects
                parent_category = Category.objects.filter(id=parent_id).first() if parent_id else None
                category_type = CategoryType.objects.filter(id=category_type_id).first()

                # Update category
                category.name = name
                category.slug = new_slug
                category.parent_category = parent_category
                category.category_type = category_type
                category.status = status
                category.description = description
                category.meta_title = meta_title
                category.meta_key = meta_key
                category.meta_description = meta_description
                
                # Handle image uploads for update
                if 'banner' in request.FILES:
                    category.banner = request.FILES['banner']
                if 'thumbnail_small' in request.FILES:
                    category.thumbnail_small = request.FILES['thumbnail_small']
                if 'icon' in request.FILES:
                    category.icon = request.FILES['icon']

                category.save()

                return JsonResponse({
                    'success': True, 
                    'message': 'Category updated successfully!',
                    'category': {
                        'id': category.id,
                        'slug': category.slug,
                        'name': category.name,
                        'description': category.description or '-',
                        'category_type': category.category_type.name if category.category_type else '-'
                    }
                })
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        elif action == 'delete_category':
            slug = request.POST.get('slug')
            try:
                category = get_object_or_404(Category, slug=slug)
                category_name = category.name
                category.delete()
                return JsonResponse({
                    'success': True, 
                    'message': f'Category "{category_name}" deleted successfully!'
                })
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        else:
            # Handle regular form submission (Add Category)
            name = request.POST.get('name')
            slug = request.POST.get('slug')
            parent_id = request.POST.get('parent_category')
            category_type_id = request.POST.get('category_type')
            status = request.POST.get('status')
            description = request.POST.get('description')
            meta_title = request.POST.get('meta_title')
            meta_key = request.POST.get('meta_key')
            meta_description = request.POST.get('meta_description')

            parent_category = Category.objects.filter(id=parent_id).first() if parent_id else None
            category_type = CategoryType.objects.filter(id=category_type_id).first()

            try:
                category = Category.objects.create(
                    name=name,
                    slug=slug,
                    parent_category=parent_category,
                    category_type=category_type,
                    status=status,
                    description=description,
                    meta_title=meta_title,
                    meta_key=meta_key,
                    meta_description=meta_description,
                )
                
                # Handle image uploads
                if 'banner' in request.FILES:
                    category.banner = request.FILES['banner']
                if 'thumbnail_small' in request.FILES:
                    category.thumbnail_small = request.FILES['thumbnail_small']
                if 'icon' in request.FILES:
                    category.icon = request.FILES['icon']
                
                category.save()
                messages.success(request, "Category added successfully!")
                return redirect('category')
            except Exception as e:
                messages.error(request, f"Error: {e}")

    categories = Category.objects.all()
    category_types = CategoryType.objects.all()

    context = {
        "breadcrumb": {"title": "Category", "parent": "Ecommerce", "child": "Category"},
        "categories": categories,
        "category_types": category_types,
    }
    return render(request, "category/category.html", context)




@login_required(login_url="/admin-dashboard/login_home")
def order_history(request):
    orders = Order.objects.all().order_by('-created_at')
     # ADD ONLY THIS LINE:
    unviewed_count = OrderNotification.objects.filter(is_viewed=False).count()
     # ADD ONLY THIS LINE:
    unviewed_ids = list(OrderNotification.objects.filter(is_viewed=False).values_list("order_id", flat=True))
    context = {
        "breadcrumb": {"title": "Order History", "parent": "Ecommerce", "child": "Order History"},
        "orders": orders,
        "unviewed_count": unviewed_count  ,# ADD ONLY THIS LINE
        "unviewed_ids": unviewed_ids,  # ADD ONLY THIS LINE
    }
    return render(request, "orders/order-history.html", context)


@login_required(login_url="/admin-dashboard/login_home")
def order_details(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    # ADD ONLY THIS BLOCK:
    try:
        notification = OrderNotification.objects.get(order=order)
        if not notification.is_viewed:
            notification.is_viewed = True
            notification.viewed_by = request.user
            notification.viewed_at = timezone.now()
            notification.save()
    except OrderNotification.DoesNotExist:
        OrderNotification.objects.create(
            order=order,
            is_viewed=True,
            viewed_by=request.user,
            viewed_at=timezone.now()
        )
    order_items = []
    for vendor_order in order.vendor_orders.all():
        for item in vendor_order.items.all():
            item.total_price = item.final_price * item.quantity
            item.vendor = vendor_order.vendor
            order_items.append(item)

    context = {
        "breadcrumb": {"title": "Order Details", "parent": "Ecommerce", "child": "Order Details"},
        "order": order,
        "order_items": order_items,
    }
    return render(request, "orders/order-details.html", context)




@login_required(login_url="/admin-dashboard/login_home")
def get_order_count(request):
    unviewed_count = OrderNotification.objects.filter(is_viewed=False).count()
    return JsonResponse({'count': unviewed_count})



@require_POST
@login_required(login_url="/admin-dashboard/login_home")
def mark_order_viewed(request):
    order_id = request.POST.get("order_id")
    if order_id:
        OrderNotification.objects.filter(order_id=order_id, is_viewed=False).update(is_viewed=True)
    return JsonResponse({"status": "ok"})


@require_POST
@login_required
def reject_product(request):
    product_id = request.POST.get("product_id")
    reason = request.POST.get("rejectReason")
    plain_reason = strip_tags(reason).strip()
    
    print('rejection reason: ', plain_reason)

    if not product_id or not plain_reason:
        return JsonResponse({"success": False, "message": "Product ID and rejection reason are required."})

    try:
        product = Product.objects.get(pk=product_id)
        product.publish_status = 3  # Rejected
        product.rejection_reason = reason
        product.save(update_fields=["publish_status", "rejection_reason"])
        return JsonResponse({"success": True, "message": "Product has been rejected successfully."})
    except Product.DoesNotExist:
        return JsonResponse({"success": False, "message": "Product not found."})
    

@require_POST
def change_publish_status(request):
    product_id = request.POST.get("product_id")
    status = request.POST.get("status")

    try:
        product = Product.objects.get(id=product_id)
        product.status = status
        product.save()
        return JsonResponse({"success": True})
    except Product.DoesNotExist:
        return JsonResponse({"success": False, "message": "Product not found"})
    
    
def update_approval_status(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        product = get_object_or_404(Product, pk=product_id)
        status = int(request.POST.get("approval"))

        if status == 3:
            # Reject selected → frontend handles modal
            return JsonResponse({"show_modal": True})

        # Pending or Approve → update directly
        product.publish_status = status
        product.rejection_reason = ""  # clear previous rejection reason
        product.save()

        return JsonResponse({
            "success": True,
            "message": f"Product status updated to {product.get_publish_status_display()}"
        })









def vendorOrder(request):
    return render (request,'vendor_Order/orderList.html')


from django.http import JsonResponse, HttpResponseBadRequest
def notify_vendor_item(request):
    """Admin click → notify vendor about a single item."""
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    data = json.loads(request.body.decode("utf-8"))
    item_id = data.get("item_id")
    order_id = data.get("order_id")

    item = get_object_or_404(OrderItem, id=item_id, vendor_order__order_id=order_id)
    vendor_order = item.vendor_order
    order = vendor_order.order
    vendor = vendor_order.vendor

    notice, created = VendorOrderNotice.objects.get_or_create(
        order=order,
        vendor_order=vendor_order,
        item=item,
        vendor=vendor,
        defaults={"notified_by": request.user}
    )
    return JsonResponse({"ok": True, "created": created})


@login_required
def vendor_orders_api(request):
    """Vendors fetch their notified items only."""
    qs = VendorOrderNotice.objects.filter(vendor=request.user).select_related(
        "order", "item__product"
    ).order_by("-created_at")

    data = []
    for n in qs:
        data.append({
            "order_number": n.order.order_number,
            "order_date": n.order.created_at.strftime("%d %b %Y %I:%M %p"),
            "product_title": n.item.product.title,
            "image": n.item.product.thumbnail_image.url if n.item.product.thumbnail_image else "",
            "quantity": n.item.quantity,
            "price": str(n.item.final_price),
            "subtotal": str(n.item.get_total_price()),
            "detail_url": f"/orders/{n.order.id}/"
        })
    return JsonResponse({"data": data})




@receiver(post_save, sender=OrderVendor)
def create_vendor_order_notification(sender, instance, created, **kwargs):
    if created:
        VendorOrderNotification.objects.create(vendor_order=instance)
@login_required(login_url="/admin-dashboard/login_home")
def get_vendor_order_count(request):
    unviewed_count = VendorOrderNotification.objects.filter(
        vendor_order__vendor=request.user,
        is_viewed=False
    ).count()
    return JsonResponse({'count': unviewed_count})


@require_POST
@login_required(login_url="/admin-dashboard/login_home")
def mark_vendor_order_viewed(request):
    vendor_order_id = request.POST.get("vendor_order_id")
    if vendor_order_id:
        VendorOrderNotification.objects.filter(
            vendor_order_id=vendor_order_id,
            is_viewed=False
        ).update(
            is_viewed=True,
            viewed_by=request.user,
            viewed_at=timezone.now()
        )
    return JsonResponse({"status": "ok"})












@login_required
def deliverytype(request):
    user = request.user  # Logged-in user
    
    # Only root/admin can manage delivery types
    if user.user_type != 0:
        return JsonResponse({'status': 'error', 'message': 'You do not have permission to manage delivery types.'})

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')

            if action == 'add':
                name = data.get('name', '').strip()
                if not name:
                    return JsonResponse({'status': 'error', 'message': 'Name is required'})

                # Check if delivery type already exists
                if DeliveryType.objects.filter(name__iexact=name, vendor=user).exists():
                    return JsonResponse({'status': 'error', 'message': 'Delivery type already exists'})

                delivery_type = DeliveryType.objects.create(
                    name=name,
                    vendor=user
                )
                return JsonResponse({'status': 'success', 'message': 'Delivery type added successfully'})

            elif action == 'edit':
                type_id = data.get('id')
                name = data.get('name', '').strip()

                if not name:
                    return JsonResponse({'status': 'error', 'message': 'Name is required'})

                delivery_type = get_object_or_404(DeliveryType, id=type_id, vendor=user)

                if DeliveryType.objects.filter(name__iexact=name, vendor=user).exclude(id=type_id).exists():
                    return JsonResponse({'status': 'error', 'message': 'Delivery type already exists'})

                delivery_type.name = name
                delivery_type.slug = slugify(name)
                delivery_type.save()
                
                return JsonResponse({'status': 'success', 'message': 'Delivery type updated successfully'})

            elif action == 'delete':
                type_id = data.get('id')
                delivery_type = get_object_or_404(DeliveryType, id=type_id, vendor=user)

                if DeliveryCharge.objects.filter(delivery_type=delivery_type).exists():
                    return JsonResponse({'status': 'error', 'message': 'Cannot delete. Delivery charges exist for this type.'})

                delivery_type.delete()
                return JsonResponse({'status': 'success', 'message': 'Delivery type deleted successfully'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    # GET request: show all delivery types
    delivery_types = DeliveryType.objects.filter(vendor=user).order_by('-created_at')
    return render(request, 'delivery/delivery_type.html', {'delivery_types': delivery_types})


@login_required
def get_delivery_types(request):
    types = DeliveryType.objects.values("id", "name")  # only return the fields you need
    return JsonResponse({"types": list(types)})



@login_required
def deliveryCharge(request):
    vendor = request.user  # The logged-in user is the vendor
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'add':
                delivery_type_id = data.get('delivery_type')
                amount = data.get('amount', '').strip()
                
                if not delivery_type_id or not amount:
                    return JsonResponse({'status': 'error', 'message': 'All fields are required'})
                
                try:
                    amount = float(amount)
                    if amount < 0:
                        return JsonResponse({'status': 'error', 'message': 'Amount must be positive'})
                except ValueError:
                    return JsonResponse({'status': 'error', 'message': 'Invalid amount format'})
                
                delivery_type = get_object_or_404(DeliveryType, id=delivery_type_id)
                
                # Check if charge already exists for this delivery type
                if DeliveryCharge.objects.filter(delivery_type=delivery_type, vendor=vendor).exists():
                    return JsonResponse({'status': 'error', 'message': 'Charge already exists for this delivery type'})
                
                DeliveryCharge.objects.create(
                    delivery_type=delivery_type,
                    amount=amount,
                    vendor=vendor
                )
                return JsonResponse({'status': 'success', 'message': 'Delivery charge added successfully'})
            
            elif action == 'edit':
                charge_id = data.get('id')
                delivery_type_id = data.get('delivery_type')
                amount = data.get('amount', '').strip()
                
                if not delivery_type_id or not amount:
                    return JsonResponse({'status': 'error', 'message': 'All fields are required'})
                
                try:
                    amount = float(amount)
                    if amount < 0:
                        return JsonResponse({'status': 'error', 'message': 'Amount must be positive'})
                except ValueError:
                    return JsonResponse({'status': 'error', 'message': 'Invalid amount format'})
                
                delivery_charge = get_object_or_404(DeliveryCharge, id=charge_id, vendor=vendor)
                delivery_type = get_object_or_404(DeliveryType, id=delivery_type_id, vendor=vendor)
                
                # Check if another charge exists for this delivery type (excluding current)
                if DeliveryCharge.objects.filter(delivery_type=delivery_type, vendor=vendor).exclude(id=charge_id).exists():
                    return JsonResponse({'status': 'error', 'message': 'Charge already exists for this delivery type'})
                
                delivery_charge.delivery_type = delivery_type
                delivery_charge.amount = amount
                delivery_charge.save()
                
                return JsonResponse({'status': 'success', 'message': 'Delivery charge updated successfully'})
            
            elif action == 'delete':
                charge_id = data.get('id')
                delivery_charge = get_object_or_404(DeliveryCharge, id=charge_id, vendor=vendor)
                delivery_charge.delete()
                return JsonResponse({'status': 'success', 'message': 'Delivery charge deleted successfully'})
            
        except Exception as e:
            print(f"Error in deliveryCharge POST: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    # GET request
    delivery_charges = DeliveryCharge.objects.filter(vendor=vendor).select_related('delivery_type').order_by('-created_at')
    delivery_types = DeliveryType.objects.filter(status=True)
    
    context = {
        'delivery_charges': delivery_charges,
        'delivery_types': delivery_types
    }
    return render(request, 'delivery/delivery.html', context)





















































# Built in views in the template
@login_required(login_url="/admin-dashboard/login_home")
def dashboard_02(request):
    context = { "breadcrumb":{"title":"E-Commerce","parent":"Dashboard","child":"E-Commerce"},}
    return render(request,"general/dashboard/dashboard-02.html",context)


@login_required(login_url="/admin-dashboard/login_home")
def dashboard_03(request):
    context = { "breadcrumb":{"title":"Online Course","parent":"Dashboard","child":"Online Course"},}
    return render(request,"general/dashboard/dashboard-03.html",context)


@login_required(login_url="/admin-dashboard/login_home")
def dashboard_04(request):
    context = { "breadcrumb":{"title":"Crypto","parent":"Dashboard","child":"Crypto"},}
    return render(request,"general/dashboard/dashboard-04.html",context)


@login_required(login_url="/admin-dashboard/login_home")
def dashboard_05(request):
    context = { "breadcrumb":{"title":"Social","parent":"Dashboard","child":"Social"},}
    return render(request,"general/dashboard/dashboard-05.html",context)


@login_required(login_url="/admin-dashboard/login_home")
def dashboard_06(request):
    context = { "breadcrumb":{"title":"NFT","parent":"Dashboard","child":"NFT"},}
    return render(request,"general/dashboard/dashboard-06.html",context)


@login_required(login_url="/admin-dashboard/login_home")
def dashboard_07(request):
    context = { "breadcrumb":{"title":"School Management","parent":"Dashboard","child":"School Management"},}
    return render(request,"general/dashboard/dashboard-07.html",context)


@login_required(login_url="/admin-dashboard/login_home")
def dashboard_08(request):
    context = { "breadcrumb":{"title":"POS","parent":"Dashboard","child":"POS"},}
    return render(request,"general/dashboard/dashboard-08.html",context)


@login_required(login_url="/admin-dashboard/login_home")
def dashboard_09(request):
    context = { "breadcrumb":{"title":"CRM","parent":"Dashboard","child":"CRM"},}
    return render(request,"general/dashboard/dashboard-09.html",context)


@login_required(login_url="/admin-dashboard/login_home")
def dashboard_10(request):
    context = { "breadcrumb":{"title":"Analytics","parent":"Dashboard","child":"Analytics"},}
    return render(request,"general/dashboard/dashboard-10.html",context)


@login_required(login_url="/admin-dashboard/login_home")
def dashboard_11(request):
    context = { "breadcrumb":{"title":"HR Dashboard","parent":"Dashboard","child":"HR Dashboard"},}
    return render(request,"general/dashboard/dashboard-11.html",context)


# #---------------Widgets

@login_required(login_url="/admin-dashboard/login_home")
def general_widget(request):
    context = { "breadcrumb":{"title":"General","parent":"Widgets", "child":"General"}} 
    return render(request,"general/widget/general-widget.html",context)

@login_required(login_url="/admin-dashboard/login_home")
def chart_widget(request):
    context = { "breadcrumb":{"title":"Chart","parent":"Widgets", "child":"Chart"}} 
    return render(request,"general/widget/chart-widget.html",context)


# #-----------------Layout
@login_required(login_url="/admin-dashboard/login_home")
def box_layout(request):
    context = {'layout':'box-layout', "breadcrumb":{"title":"Box Layout","parent":"Page Layout", "child":"Box Layout"}}
    return render(request,"general/page-layout/box-layout.html",context)

@login_required(login_url="/admin-dashboard/login_home")
def layout_rtl(request):
    context = {'layout':'rtl', "breadcrumb":{"title":"RTL Layout","parent":"Page Layout", "child":"RTL Layout"}}
    return render(request,"general/page-layout/layout-rtl.html",context)

@login_required(login_url="/admin-dashboard/login_home")
def layout_dark(request):
    context = {'layout':'dark-only', "breadcrumb":{"title":"Layout Dark","parent":"Page Layout", "child":"Layout Dark"}}
    return render(request,"general/page-layout/layout-dark.html",context)

@login_required(login_url="/admin-dashboard/login_home")
def hide_on_scroll(request):
    context = { "breadcrumb":{"title":"Hide Menu On Scroll","parent":"Page Layout", "child":"Hide Menu On Scroll"}}
    return render(request,"general/page-layout/hide-on-scroll.html",context)


@login_required(login_url="/admin-dashboard/login_home")
def footer_light(request):
    context = { "breadcrumb":{"title":"Footer Light","parent":"Page Layout", "child":"Footer Light"}}
    return render(request,"general/page-layout/footer-light.html",context)

@login_required(login_url="/admin-dashboard/login_home")
def footer_dark(request):
    context = { "breadcrumb":{"title":"Footer Dark","parent":"Page Layout", "child":"Footer Dark"}}
    return render(request,"general/page-layout/footer-dark.html",context)

@login_required(login_url="/admin-dashboard/login_home")
def footer_fixed(request):
    context = { "breadcrumb":{"title":"Footer Fixed","parent":"Page Layout", "child":"Footer Fixed"}}
    return render(request,"general/page-layout/footer-fixed.html",context)


#--------------------------------Applications---------------------------------

#---------------------Project 
@login_required(login_url="/admin-dashboard/login_home")
def project_details(request):
    context = { "breadcrumb":{"title":"Project Details","parent":"Projects", "child":"Project Details"}}
    return render(request,"applications/projects/scope-project.html",context)


@login_required(login_url="/admin-dashboard/login_home")
def projects(request):
    context = { "breadcrumb":{"title":"Project List","parent":"Projects", "child":"Project List"}}
    return render(request,"applications/projects/project-list.html",context)
    
@login_required(login_url="/admin-dashboard/login_home")
def projectcreate(request):
    context = { "breadcrumb":{"title":"Project Create","parent":"Projects", "child":"Project Create"}}
    return render(request,"applications/projects/projectcreate.html",context)


#-------------------File Manager
@login_required(login_url="/admin-dashboard/login_home")
def file_manager(request):
    context = { "breadcrumb":{"title":"File Manager","parent":"Apps", "child":"File Manager"}}
    return render(request,"applications/file-manager/file-manager.html",context)

#------------------------Kanban Board
@login_required(login_url="/admin-dashboard/login_home")
def kanban(request):
    context = { "breadcrumb":{"title":"Kanban Board","parent":"Apps", "child":"Kanban Board"}}
    return render(request,"applications/kanban/kanban.html",context)


#------------------------ Ecommerce





@login_required(login_url="/admin-dashboard/login_home")
def seller_list(request):
    context = { "breadcrumb":{"title":"Seller List","parent":"Ecommerce", "child":"Seller List"}}
    return render(request,"applications/ecommerce/seller/seller-list.html",context)


@login_required(login_url="/admin-dashboard/login_home")
def seller_details(request):
    context = { "breadcrumb":{"title":"Seller Details","parent":"Ecommerce", "child":"Seller Details"}}
    return render(request,"applications/ecommerce/seller/seller-details.html",context)



       
           
@login_required(login_url="/admin-dashboard/login_home")           
def invoice_1(request):
    return render(request,"applications/ecommerce/invoice-1.html")

@login_required(login_url="/admin-dashboard/login_home")
def invoice_2(request):
    return render(request,"applications/ecommerce/invoice-2.html")

@login_required(login_url="/admin-dashboard/login_home")
def invoice_3(request):
    return render(request,"applications/ecommerce/invoice-3.html")

@login_required(login_url="/admin-dashboard/login_home")
def invoice_4(request):
    return render(request,"applications/ecommerce/invoice-4.html")

@login_required(login_url="/admin-dashboard/login_home")
def invoice_5(request):
    return render(request,"applications/ecommerce/invoice-5.html")

@login_required(login_url="/admin-dashboard/login_home")
def invoice_6(request):
    context = { "breadcrumb":{"title":"Invoice","parent":"Ecommerce", "child":"Invoice"}}
    return render(request,"applications/ecommerce/invoice-template.html",context)

@login_required(login_url="/admin-dashboard/login_home")
def cart(request):
    context = { "breadcrumb":{"title":"Cart","parent":"Ecommerce", "child":"Cart"}}
    return render(request,"applications/ecommerce/cart.html",context)
      
@login_required(login_url="/admin-dashboard/login_home")
def list_wish(request):
    context = { "breadcrumb":{"title":"Wishlist","parent":"Ecommerce", "child":"Wishlist"}}
    return render(request,"applications/ecommerce/list-wish.html",context)
     
@login_required(login_url="/admin-dashboard/login_home")
def checkout(request):
    context = { "breadcrumb":{"title":"Checkout","parent":"Ecommerce", "child":"Checkout"}}
    return render(request,"applications/ecommerce/checkout.html",context)


#------------------------ Letter-Box
@login_required(login_url="/admin-dashboard/login_home")
def mail_box(request):
    context = { "breadcrumb":{"title":"Mail Box","parent":"Email", "child":"Mail Box"}}
    return render(request,"applications/mail-box/mail-box.html",context)


#--------------------------------chat
@login_required(login_url="/admin-dashboard/login_home")
def private_chat(request):
    context = { "breadcrumb":{"title":"Private Chat","parent":"Chat", "child":"Private Chat"}}
    return render(request,"applications/chat/private-chat.html",context)
     
@login_required(login_url="/admin-dashboard/login_home")
def group_chat(request):
    context = { "breadcrumb":{"title":"Group Chat","parent":"Chat", "child":"Group Chat"}}
    return render(request,"applications/chat/group-chat.html",context)



#---------------------------------user
@login_required(login_url="/admin-dashboard/login_home")
def user_profile(request):
    context = { "breadcrumb":{"title":"User Profile","parent":"Users", "child":"User Profile"}}
    return render(request,"applications/users/user-profile.html",context)
    
@login_required(login_url="/admin-dashboard/login_home")
def edit_profile(request):
    context = { "breadcrumb":{"title":"User Edit","parent":"Users", "child":"User Edit"}}
    return render(request,"applications/users/edit-profile.html",context)
       
@login_required(login_url="/admin-dashboard/login_home")
def user_cards(request):
    context = { "breadcrumb":{"title":"User Cards","parent":"Users", "child":"User Cards"}}
    return render(request,"applications/users/user-cards.html",context)



#------------------------bookmark
@login_required(login_url="/admin-dashboard/login_home")
def bookmark(request):
    context = { "breadcrumb":{"title":"Bookmarks","parent":"Apps", "child":"Bookmarks"}}
    return render(request,"applications/bookmark/bookmark.html",context)


#------------------------contacts
@login_required(login_url="/admin-dashboard/login_home")
def contacts(request):
    context = { "breadcrumb":{"title":"Contacts","parent":"Apps", "child":"Contacts"}}
    return render(request,"applications/contacts/contacts.html",context)


#------------------------task
@login_required(login_url="/admin-dashboard/login_home")
def task(request):
    context = { "breadcrumb":{"title":"Tasks","parent":"Apps", "child":"Tasks"}}
    return render(request,"applications/task/task.html",context)
    

#------------------------calendar
@login_required(login_url="/admin-dashboard/login_home")
def calendar_basic(request):
    context = { "breadcrumb":{"title":"Calender Basic","parent":"Apps", "child":"Calender Basic"}}
    return render(request,"applications/calendar/calendar-basic.html",context)
    

#------------------------social-app
@login_required(login_url="/admin-dashboard/login_home")
def social_app(request):
    context = { "breadcrumb":{"title":"Social App","parent":"Apps", "child":"Social App"}}
    return render(request,"applications/social-app/social-app.html",context)


#------------------------to-do
@login_required(login_url="/admin-dashboard/login_home")
def to_do(request):
    context = { "breadcrumb":{"title":"To-Do","parent":"Apps", "child":"To-Do"}}
    return render(request,"applications/to-do/to-do.html",context)
    

#------------------------search
@login_required(login_url="/admin-dashboard/login_home")
def search(request):
    context = { "breadcrumb":{"title":"Search Result","parent":"Search Pages", "child":"Search Result"}}
    return render(request,"applications/search/search.html",context)



#--------------------------------Forms & Table-----------------------------------------------
#--------------------------------Forms------------------------------------
#------------------------form-controls


@login_required(login_url="/admin-dashboard/login_home")
def form_validation(request):
    context = { "breadcrumb":{"title":"Validation Forms","parent":"Form Controls", "child":"Validation Forms"}}
    return render(request,"forms-table/forms/form-controls/form-validation.html",context)


@login_required(login_url="/admin-dashboard/login_home")
def base_input(request):
    context = { "breadcrumb":{"title":"Base Inputs","parent":"Form Controls", "child":"Base Inputs"}}
    return render(request,"forms-table/forms/form-controls/base-input.html",context)    


@login_required(login_url="/admin-dashboard/login_home")
def radio_checkbox_control(request):
    context = { "breadcrumb":{"title":"Checkbox & Radio","parent":"Form Controls", "child":"Checkbox & Radio"}}
    return render(request,"forms-table/forms/form-controls/radio-checkbox-control.html",context)

    
@login_required(login_url="/admin-dashboard/login_home")
def input_group(request):
    context = { "breadcrumb":{"title":"Input Groups","parent":"Form Controls", "child":"Input Groups"}}
    return render(request,"forms-table/forms/form-controls/input-group.html",context)


@login_required(login_url="/admin-dashboard/login_home")
def input_mask(request):
    context = { "breadcrumb":{"title":"Input Mask","parent":"Form Controls", "child":"Input Mask"}}
    return render(request,"forms-table/forms/form-controls/input-mask.html",context)

    
@login_required(login_url="/admin-dashboard/login_home")
def megaoptions(request):
    context = { "breadcrumb":{"title":"Mega Options","parent":"Form Controls", "child":"Mega Options"}}
    return render(request,"forms-table/forms/form-controls/megaoptions.html",context)    




#---------------------------form widgets

@login_required(login_url="/admin-dashboard/login_home")
def datepicker(request):
    context = { "breadcrumb":{"title":"Datepicker","parent":"Form Widgets", "child":"Datepicker"}}
    return render(request,"forms-table/forms/form-widgets/datepicker.html",context)


@login_required(login_url="/admin-dashboard/login_home")    
def touchspin(request):
    context = { "breadcrumb":{"title":"Touchspin","parent":"Form Widgets", "child":"Touchspin"}}
    return render(request,'forms-table/forms/form-widgets/touchspin.html',context)


@login_required(login_url="/admin-dashboard/login_home")
def select2(request):
    context = { "breadcrumb":{"title":"Select2","parent":"Form Widgets", "child":"Select2"}}
    return render(request,'forms-table/forms/form-widgets/select2.html',context)


@login_required(login_url="/admin-dashboard/login_home")      
def switch(request):
    context = { "breadcrumb":{"title":"Switch","parent":"Form Widgets", "child":"Switch"}}
    return render(request,'forms-table/forms/form-widgets/switch.html',context)
      

@login_required(login_url="/admin-dashboard/login_home")      
def typeahead(request):
    context = { "breadcrumb":{"title":"Typeahead","parent":"Form Widgets", "child":"Typeahead"}}
    return render(request,'forms-table/forms/form-widgets/typeahead.html',context)
      

@login_required(login_url="/admin-dashboard/login_home")    
def clipboard(request):
    context = { "breadcrumb":{"title":"Clipboard","parent":"Form Widgets", "child":"Clipboard"}}
    return render(request,'forms-table/forms/form-widgets/clipboard.html',context)
     
     
#-----------------------form layout

@login_required(login_url="/admin-dashboard/login_home")
def form_wizard_one(request):
    context = { "breadcrumb":{"title":"Form Wizard 1","parent":"Form Layout", "child":"Form Wizard 1"}}
    return render(request,'forms-table/forms/form-layout/form-wizard.html',context) 


@login_required(login_url="/admin-dashboard/login_home")
def form_wizard_two(request):
    context = { "breadcrumb":{"title":"Form Wizard 2","parent":"Form Layout", "child":"Form Wizard 2"}}
    return render(request,'forms-table/forms/form-layout/form-wizard-two.html',context) 


@login_required(login_url="/admin-dashboard/login_home")
def two_factor(request):
    context = { "breadcrumb":{"title":"Two Factor","parent":"Form Layout", "child":"Two Factor"}}
    return render(request,'forms-table/forms/form-layout/two-factor.html',context)



#----------------------------------------------------Table------------------------------------------
#------------------------bootstrap table

@login_required(login_url="/admin-dashboard/login_home")
def basic_table(request):
    context = { "breadcrumb":{"title":"Bootstrap Basic Tables","parent":"Bootstrap Tables", "child":"Bootstrap Basic Tables "}}
    return render(request,'forms-table/table/bootstrap-table/bootstrap-basic-table.html',context)
    

@login_required(login_url="/admin-dashboard/login_home")
def table_components(request):
    context = { "breadcrumb":{"title":"Table Components","parent":"Bootstrap Tables", "child":"Table Components"}}
    return render(request,'forms-table/table/bootstrap-table/table-components.html',context)


#------------------------data table

@login_required(login_url="/admin-dashboard/login_home")
def datatable_basic_init(request):
    context = { "breadcrumb":{"title":"Basic DataTables","parent":"Data Tables", "child":"Basic DataTables"}}
    return render(request,'forms-table/table/data-table/datatable-basic-init.html',context)
    

@login_required(login_url="/admin-dashboard/login_home")
def datatable_advance(request):
    context = { "breadcrumb":{"title":"Advance Init","parent":"Data Tables", "child":"Advance Init"}}
    return render(request,'forms-table/table/data-table/datatable-advance.html',context)
    

@login_required(login_url="/admin-dashboard/login_home")
def datatable_API(request):
    context = { "breadcrumb":{"title":"API DataTables","parent":"Data Tables", "child":"API DataTables"}}
    return render(request,'forms-table/table/data-table/datatable-API.html',context)
    

@login_required(login_url="/admin-dashboard/login_home")
def datatable_data_source(request):
    context = { "breadcrumb":{"title":"DATA Source DataTables","parent":"Data Tables", "child":"DATA Source DataTables"}}
    return render(request,'forms-table/table/data-table/datatable-data-source.html',context)


#-------------------------------EX.data-table

@login_required(login_url="/admin-dashboard/login_home")
def ext_autofill(request):
    context = { "breadcrumb":{"title":"Autofill Datatables","parent":"Extension Data Tables", "child":"Autofill Datatables"}}
    return render(request,'forms-table/table/Ex-data-table/datatable-ext-autofill.html',context)


#--------------------------------jsgrid_table

@login_required(login_url="/admin-dashboard/login_home")
def jsgrid_table(request):
    context = { "breadcrumb":{"title":"JS Grid Tables","parent":"Tables", "child":"JS Grid Tables"}}
    return render(request,'forms-table/table/js-grid-table/jsgrid-table.html',context)  




#------------------Components------UI Components-----Elements ----------->

#-----------------------------Ui kits

@login_required(login_url="/admin-dashboard/login_home")
def typography(request):
    context = { "breadcrumb":{"title":"Typography","parent":"Ui Kits", "child":"Typography"}}
    return render(request,'components/ui-kits/typography.html', context)


@login_required(login_url="/admin-dashboard/login_home")
def avatars(request):
    context = { "breadcrumb":{"title":"Avatars","parent":"Ui Kits", "child":"Avatars"}}
    return render(request,'components/ui-kits/avatars.html', context)


@login_required(login_url="/admin-dashboard/login_home")
def divider(request):
    context = { "breadcrumb":{"title":"Divider","parent":"Ui Kits", "child":"Divider"}}
    return render(request,'components/ui-kits/divider.html', context)


@login_required(login_url="/admin-dashboard/login_home")
def helper_classes(request):
    context = { "breadcrumb":{"title":"Helper Classes","parent":"Ui Kits", "child":"Helper Classes"}}
    return render(request,'components/ui-kits/helper-classes.html', context)


@login_required(login_url="/admin-dashboard/login_home")
def grid(request):
    context = { "breadcrumb":{"title":"Grid","parent":"Ui Kits", "child":"Grid"}}
    return render(request,'components/ui-kits/grid.html', context)

     
@login_required(login_url="/admin-dashboard/login_home")      
def tagpills(request):
    context = { "breadcrumb":{"title":"Tag & Pills","parent":"Ui Kits", "child":"Tag & Pills"}}
    return render(request,'components/ui-kits/tag-pills.html', context)


@login_required(login_url="/admin-dashboard/login_home")
def progressbar(request):
    context = { "breadcrumb":{"title":"Progress","parent":"Ui Kits", "child":"Progress"}}
    return render(request,'components/ui-kits/progress-bar.html', context)


@login_required(login_url="/admin-dashboard/login_home")
def modal(request):
    context = { "breadcrumb":{"title":"Modal","parent":"Ui Kits", "child":"Modal"}}
    return render(request,'components/ui-kits/modal.html', context)  


@login_required(login_url="/admin-dashboard/login_home")
def alert(request):
    context = { "breadcrumb":{"title":"Alerts","parent":"Ui Kits", "child":"Alerts"}}
    return render(request,'components/ui-kits/alert.html', context)


@login_required(login_url="/admin-dashboard/login_home")   
def popover(request):
    context = { "breadcrumb":{"title":"Popover","parent":"Ui Kits", "child":"Popover"}}
    return render(request,'components/ui-kits/popover.html', context) 


@login_required(login_url="/admin-dashboard/login_home")   
def placeholder(request):
    context = { "breadcrumb":{"title":"Placeholders","parent":"Ui Kits", "child":"Placeholders"}}
    return render(request,'components/ui-kits/placeholders.html', context) 


@login_required(login_url="/admin-dashboard/login_home")
def tooltip(request):
    context = { "breadcrumb":{"title":"Tooltip","parent":"Ui Kits", "child":"Tooltip"}}
    return render(request,'components/ui-kits/tooltip.html', context)


@login_required(login_url="/admin-dashboard/login_home")
def dropdown(request):
    context = { "breadcrumb":{"title":"Dropdowns","parent":"Ui Kits", "child":"Dropdowns"}}
    return render(request,'components/ui-kits/dropdown.html', context)   


@login_required(login_url="/admin-dashboard/login_home")
def accordion(request):
    context = { "breadcrumb":{"title":"Accordions","parent":"Ui Kits", "child":"Accordions"}}
    return render(request,'components/ui-kits/according.html', context)    

     
@login_required(login_url="/admin-dashboard/login_home")
def bootstraptab(request):
    context = { "breadcrumb":{"title":"Bootstrap Tabs","parent":"Ui Kits", "child":"Bootstrap Tabs"}}
    return render(request,'components/ui-kits/tab-bootstrap.html', context)    
    

@login_required(login_url="/admin-dashboard/login_home")
def offcanvas(request):
    context = {"breadcrumb":{"title":"Offcanvas","parent":"Ui Kits", "child":"Offcanvas"}}
    return render(request,'components/ui-kits/offcanvas.html', context) 


@login_required(login_url="/admin-dashboard/login_home")
def navigate_links(request):
    context = {"breadcrumb":{"title":"Navigate Links","parent":"Ui Kits", "child":"Navigate Links"}}
    return render(request,'components/ui-kits/navigate-links.html', context) 


@login_required(login_url="/admin-dashboard/login_home")
def lists(request):
    context = {"breadcrumb":{"title":"Lists","parent":"Ui Kits", "child":"Lists"}}
    return render(request,'components/ui-kits/list.html', context) 



#-------------------------------Bonus Ui

@login_required(login_url="/admin-dashboard/login_home")
def scrollable(request):
    context = {"breadcrumb":{"title":"Scrollable","parent":"Bonus Ui", "child":"Scrollable"}}
    return render(request,'components/bonus-ui/scrollable.html', context)
            
            
@login_required(login_url="/admin-dashboard/login_home")
def tree(request):
    context = {"breadcrumb":{"title":"Tree View","parent":"Bonus Ui", "child":"Tree View"}}
    return render(request,'components/bonus-ui/tree.html', context)


@login_required(login_url="/admin-dashboard/login_home")           
def toasts(request):
    context = {"breadcrumb":{"title":"Toasts","parent":"Bonus Ui", "child":"Toasts"}}
    return render(request,'components/bonus-ui/toasts.html', context)      

  
@login_required(login_url="/admin-dashboard/login_home")    
def blockUi(request):
    context = {"breadcrumb":{"title":"Block Ui","parent":"Bonus Ui", "child":"Block Ui"}}
    return render(request,'components/bonus-ui/block-ui.html', context)


@login_required(login_url="/admin-dashboard/login_home")    
def rating(request):
    context = {"breadcrumb":{"title":"Rating","parent":"Bonus Ui", "child":"Rating"}}
    return render(request,'components/bonus-ui/rating.html', context)
               
               
@login_required(login_url="/admin-dashboard/login_home")
def dropzone(request):
    context = {"breadcrumb":{"title":"Dropzone","parent":"Bonus Ui", "child":"Dropzone"}}
    return render(request,'components/bonus-ui/dropzone.html', context)    
    
    
@login_required(login_url="/admin-dashboard/login_home")
def tour(request):
    context = {"breadcrumb":{"title":"Tour","parent":"Bonus Ui", "child":"Tour"}}
    return render(request,'components/bonus-ui/tour.html', context)        
    
    
@login_required(login_url="/admin-dashboard/login_home")
def sweetalert2(request):
    context = {"breadcrumb":{"title":"Sweet Alert","parent":"Bonus Ui", "child":"Sweet Alert"}}
    return render(request,'components/bonus-ui/sweet-alert2.html', context)    
    
    
@login_required(login_url="/admin-dashboard/login_home")
def animatedmodal(request):
    context = {"breadcrumb":{"title":"Animated Modal","parent":"Bonus Ui", "child":"Animated Modal"}}
    return render(request,'components/bonus-ui/modal-animated.html', context)     


@login_required(login_url="/admin-dashboard/login_home")
def owlcarousel(request):
    context = {"breadcrumb":{"title":"Owl Carousel","parent":"Bonus Ui", "child":"Owl Carousel"}}
    return render(request,'components/bonus-ui/owl-carousel.html', context)     


@login_required(login_url="/admin-dashboard/login_home")
def ribbons(request):
    context = {"breadcrumb":{"title":"Ribbons","parent":"Bonus Ui", "child":"Ribbons"}}
    return render(request,'components/bonus-ui/ribbons.html', context) 



@login_required(login_url="/admin-dashboard/login_home")
def pagination(request):
    context = {"breadcrumb":{"title":"Paginations","parent":"Bonus Ui", "child":"Paginations"}}
    return render(request,'components/bonus-ui/pagination.html', context)  


@login_required(login_url="/admin-dashboard/login_home")
def scrollspy(request):
    context = {"breadcrumb":{"title":"ScrollSpy","parent":"Bonus Ui", "child":"ScrollSpy"}}
    return render(request,'components/bonus-ui/scrollspy.html', context)  


@login_required(login_url="/admin-dashboard/login_home")
def breadcrumb(request):
    context = {"breadcrumb":{"title":"Breadcrumb","parent":"Bonus Ui", "child":"Breadcrumb"}}
    return render(request,'components/bonus-ui/breadcrumb.html', context)  

    
@login_required(login_url="/admin-dashboard/login_home")
def rangeslider(request):
    context = {"breadcrumb":{"title":"Range Slider","parent":"Bonus Ui", "child":"Range Slider"}}
    return render(request,'components/bonus-ui/range-slider.html', context)  

   
@login_required(login_url="/admin-dashboard/login_home")
def ratios(request):
    context = {"breadcrumb":{"title":"Ratios","parent":"Bonus Ui", "child":"Ratios"}}
    return render(request,'components/bonus-ui/ratios.html', context)     
    
    
@login_required(login_url="/admin-dashboard/login_home")
def imagecropper(request):
    context = {"breadcrumb":{"title":"Image Cropper","parent":"Bonus Ui", "child":"Image Cropper"}}
    return render(request,'components/bonus-ui/image-cropper.html', context)      
    

@login_required(login_url="/admin-dashboard/login_home")
def basiccard(request):
    context = {"breadcrumb":{"title":"Basic Card","parent":"Bonus Ui", "child":"Basic Card"}}
    return render(request,'components/bonus-ui/basic-card.html', context)
                    
                    
@login_required(login_url="/admin-dashboard/login_home")
def creativecard(request):
    context = {"breadcrumb":{"title":"Creative Card","parent":"Bonus Ui", "child":"Creative Card"}}
    return render(request,'components/bonus-ui/creative-card.html', context)  
       

@login_required(login_url="/admin-dashboard/login_home")
def draggablecard(request):
    context = {"breadcrumb":{"title":"Draggabble Card","parent":"Bonus Ui", "child":"Draggabble Card"}}
    return render(request,'components/bonus-ui/draggable-card.html', context)       
    
    
@login_required(login_url="/admin-dashboard/login_home")    
def timeline(request):
    context = {"breadcrumb":{"title":"Timeline","parent":"Bonus Ui", "child":"Timeline"}}
    return render(request,'components/bonus-ui/timeline-v-1.html', context)   


#---------------------------------Animation


@login_required(login_url="/admin-dashboard/login_home")
def animate(request):
    context = {"breadcrumb":{"title":"Animate","parent":"Animation", "child":"Animate"}}
    return render(request,'components/animation/animate.html', context)
            
            
@login_required(login_url="/admin-dashboard/login_home")
def scrollreval(request):
    context = {"breadcrumb":{"title":"Scroll Reveal","parent":"Animation", "child":"Scroll Reveal"}}
    return render(request,'components/animation/scroll-reval.html', context)        
    

@login_required(login_url="/admin-dashboard/login_home")
def AOS(request):
    context = {"breadcrumb":{"title":"AOS Animation","parent":"Animation", "child":"AOS Animation"}}
    return render(request,'components/animation/AOS.html', context)
            

@login_required(login_url="/admin-dashboard/login_home")
def tilt(request):
    context = {"breadcrumb":{"title":"Tilt Animation","parent":"Animation", "child":"Tilt Animation"}}
    return render(request,'components/animation/tilt.html', context)        
    
    
@login_required(login_url="/admin-dashboard/login_home")
def wow(request):
    context = {"breadcrumb":{"title":"Wow Animation","parent":"Animation", "child":"Wow Animation"}}
    return render(request,'components/animation/wow.html', context)   


@login_required(login_url="/admin-dashboard/login_home")
def flashicon(request):
    context = {"breadcrumb":{"title":"Flash Icons","parent":"Animation", "child":"Flash Icons"}}
    return render(request,'components/icons/flash-icon.html', context) 



#--------------------------Icons

@login_required(login_url="/admin-dashboard/login_home")
def flagicon(request):
    context = {"breadcrumb":{"title":"Flag Icons","parent":"Icons", "child":"Flag Icons"}}
    return render(request,'components/icons/flag-icon.html', context) 


@login_required(login_url="/admin-dashboard/login_home")
def fontawesome(request):
    context = {"breadcrumb":{"title":"Font Awesome Icon","parent":"Icons", "child":"Font Awesome Icon"}}
    return render(request,'components/icons/font-awesome.html', context) 
    

@login_required(login_url="/admin-dashboard/login_home")
def icoicon(request):
    context = {"breadcrumb":{"title":"Ico Icon","parent":"Icons", "child":"Ico Icon"}}
    return render(request,'components/icons/ico-icon.html', context) 

 
@login_required(login_url="/admin-dashboard/login_home")
def themify(request):
    context = {"breadcrumb":{"title":"Themify Icon","parent":"Icons", "child":"Themify Icon"}}
    return render(request,'components/icons/themify-icon.html', context)  


@login_required(login_url="/admin-dashboard/login_home")    
def feather(request):
    context = {"breadcrumb":{"title":"Feather Icons","parent":"Icons", "child":"Feather Icons"}}
    return render(request,'components/icons/feather-icon.html', context) 
    
    
@login_required(login_url="/admin-dashboard/login_home")
def whether(request):
    context = {"breadcrumb":{"title":"Whether Icon","parent":"Icons", "child":"Whether Icon"}}
    return render(request,'components/icons/whether-icon.html', context)  


#--------------------------------Buttons

@login_required(login_url="/admin-dashboard/login_home")
def buttons(request):
    context = {"breadcrumb":{"title":"Buttons","parent":"Buttons", "child":"Buttons"}}
    return render(request,'components/buttons/buttons.html', context)        



#-------------------------------Charts

@login_required(login_url="/admin-dashboard/login_home")
def apex(request):
    context = {"breadcrumb":{"title":"Apex Chart","parent":"Charts", "child":"Apex Chart"}}
    return render(request,'components/charts/chart-apex.html', context)    
    
    
@login_required(login_url="/admin-dashboard/login_home")         
def google(request):
    context = {"breadcrumb":{"title":"Google Chart","parent":"Charts", "child":"Google Chart"}}
    return render(request,'components/charts/chart-google.html', context)


@login_required(login_url="/admin-dashboard/login_home")         
def sparkline(request):
    context = {"breadcrumb":{"title":"Sparkline Chart","parent":"Charts", "child":"Sparkline Chart"}}
    return render(request,'components/charts/chart-sparkline.html', context)      


@login_required(login_url="/admin-dashboard/login_home")             
def flot(request):
    context = {"breadcrumb":{"title":"Flot Chart","parent":"Charts", "child":"Flot Chart"}}
    return render(request,'components/charts/chart-flot.html', context)   
    

@login_required(login_url="/admin-dashboard/login_home")
def knob(request):
    context = {"breadcrumb":{"title":"Knob Chart","parent":"Charts", "child":"Knob Chart"}}
    return render(request,'components/charts/chart-knob.html', context)     
       
       
@login_required(login_url="/admin-dashboard/login_home")         
def morris(request):
    context = {"breadcrumb":{"title":"Morris Chart","parent":"Charts", "child":"Morris Chart"}}
    return render(request,'components/charts/chart-morris.html', context)


@login_required(login_url="/admin-dashboard/login_home")      
def chartjs(request):
    context = {"breadcrumb":{"title":"ChartJS Chart","parent":"Charts", "child":"ChartJS Chart"}}
    return render(request,'components/charts/chartjs.html', context)     
    
    
@login_required(login_url="/admin-dashboard/login_home")
def chartist(request):
    context = {"breadcrumb":{"title":"Chartist Chart","parent":"Charts", "child":"Chartist Chart"}}
    return render(request,'components/charts/chartist.html', context)   


@login_required(login_url="/admin-dashboard/login_home")
def peity(request):
    context = {"breadcrumb":{"title":"Peity Chart","parent":"Charts", "child":"Peity Chart"}}
    return render(request,'components/charts/chart-peity.html', context)  



#------------------------------------------Pages-------------------------------------

#-------------------------sample-page

@login_required(login_url="/admin-dashboard/login_home")
def sample_page(request):
    context = {"breadcrumb":{"title":"Sample Page","parent":"Pages", "child":"Sample Page"}}    
    return render(request,'pages/sample-page/sample-page.html',context)
    
#--------------------------internationalization

@login_required(login_url="/admin-dashboard/login_home")
def internationalization(request):
    context = {"breadcrumb":{"title":"Internationalization","parent":"Pages", "child":"Internationalization"}}
    return render(request,'pages/internationalization/internationalization.html',context)




# ------------------------------error page

@login_required(login_url="/admin-dashboard/login_home")
def error_400(request):
    return render(request,'pages/error-pages/error-400.html')


@login_required(login_url="/admin-dashboard/login_home")
def error_401(request):
    return render(request,'pages/error-pages/error-401.html')
    

@login_required(login_url="/admin-dashboard/login_home")
def error_403(request):
    return render(request,'pages/error-pages/error-403.html')


@login_required(login_url="/admin-dashboard/login_home")
def error_404(request):
    return render(request,'pages/error-pages/error-404.html')
    

@login_required(login_url="/admin-dashboard/login_home")
def error_500(request):
    return render(request,'pages/error-pages/error-500.html')
    

@login_required(login_url="/admin-dashboard/login_home")
def error_503(request):
    return render(request,'pages/error-pages/error-503.html')
    

#----------------------------------Authentication



@login_required(login_url="/admin-dashboard/login_home")
def login_simple(request):
    return render(request,'pages/authentication/login.html')


@login_required(login_url="/admin-dashboard/login_home")
def login_one(request):
    return render(request,'pages/authentication/login_one.html')
    

@login_required(login_url="/admin-dashboard/login_home")
def login_two(request):
    return render(request,'pages/authentication/login_two.html')


@login_required(login_url="/admin-dashboard/login_home")
def login_bs_validation(request):
    return render(request,'pages/authentication/login-bs-validation.html')


@login_required(login_url="/admin-dashboard/login_home")
def login_tt_validation(request):
    return render(request,'pages/authentication/login-bs-tt-validation.html')
    

@login_required(login_url="/admin-dashboard/login_home")
def login_validation(request):
    return render(request,'pages/authentication/login-sa-validation.html')
    

@login_required(login_url="/admin-dashboard/login_home")
def sign_up(request):
    return render(request,'pages/authentication/sign-up.html')  


@login_required(login_url="/admin-dashboard/login_home")
def sign_one(request):
    return render(request,'pages/authentication/sign-up-one.html')
    

@login_required(login_url="/admin-dashboard/login_home")
def sign_two(request):
    return render(request,'pages/authentication/sign-up-two.html')


@login_required(login_url="/admin-dashboard/login_home")
def sign_wizard(request):
    return render(request,'pages/authentication/sign-up-wizard.html')    


@login_required(login_url="/admin-dashboard/login_home")
def unlock(request):
    return render(request,'pages/authentication/unlock.html')
    

@login_required(login_url="/admin-dashboard/login_home")
def forget_password(request):
    return render(request,'pages/authentication/forget-password.html')
    

@login_required(login_url="/admin-dashboard/login_home")
def reset_password(request):
    return render(request,'pages/authentication/reset-password.html')


@login_required(login_url="/admin-dashboard/login_home")
def maintenance(request):
    return render(request,'pages/authentication/maintenance.html')



#---------------------------------------comingsoon

@login_required(login_url="/admin-dashboard/login_home")
def comingsoon(request):
    return render(request,'pages/comingsoon/comingsoon.html')
    

@login_required(login_url="/admin-dashboard/login_home")
def comingsoon_video(request):
    return render(request,'pages/comingsoon/comingsoon-bg-video.html')


@login_required(login_url="/admin-dashboard/login_home")
def comingsoon_img(request):
    return render(request,'pages/comingsoon/comingsoon-bg-img.html' )
    

#----------------------------------Email-Template

@login_required(login_url="/admin-dashboard/login_home")
def basic_temp(request):
    return render(request,'pages/email-templates/basic-template.html')
    

@login_required(login_url="/admin-dashboard/login_home")
def email_header(request):
    return render(request,'pages/email-templates/email-header.html')
    

@login_required(login_url="/admin-dashboard/login_home")
def template_email(request):
    return render(request,'pages/email-templates/template-email.html')
    

@login_required(login_url="/admin-dashboard/login_home")
def template_email_2(request):
    return render(request,'pages/email-templates/template-email-2.html')


@login_required(login_url="/admin-dashboard/login_home")
def ecommerce_temp(request):
    return render(request,'pages/email-templates/ecommerce-templates.html')
    

@login_required(login_url="/admin-dashboard/login_home")
def email_order(request):
    return render(request,'pages/email-templates/email-order-success.html')   

  
  
    
@login_required(login_url="/admin-dashboard/login_home")
def pricing(request):
    context = { "breadcrumb":{"title":"Pricing","parent":"Pages", "child":"Pricing"}}
    return render(request,"pages/pricing/pricing.html",context)


#--------------------------------------faq

@login_required(login_url="/admin-dashboard/login_home")
def FAQ(request):
    context = {"breadcrumb":{"title":"FAQ","parent":"FAQ", "child":"FAQ"}}    
    return render(request,'pages/FAQ/faq.html',context)


#------------------------------------------Miscellaneous----------------- -------------------------

#--------------------------------------gallery

@login_required(login_url="/admin-dashboard/login_home")
def gallery_grid(request):
    context = {"breadcrumb":{"title":"Gallery","parent":"Gallery", "child":"Gallery"}}    
    return render(request,'miscellaneous/gallery/gallery.html',context)
    


@login_required(login_url="/admin-dashboard/login_home")
def gallery_description(request):
    context = {"breadcrumb":{"title":"Gallery Grid With Description","parent":"Gallery", "child":"Gallery Grid With Description"}}    
    return render(request,'miscellaneous/gallery/gallery-with-description.html',context)
    


@login_required(login_url="/admin-dashboard/login_home")
def masonry_gallery(request):
    context = {"breadcrumb":{"title":"Masonry Gallery","parent":"Gallery", "child":"Masonry Gallery"}}    
    return render(request,'miscellaneous/gallery/gallery-masonry.html',context)
    


@login_required(login_url="/admin-dashboard/login_home")
def masonry_disc(request):
    context = {"breadcrumb":{"title":"Masonry Gallery With Description","parent":"Gallery", "child":"Masonry Gallery With Description"}}    
    return render(request,'miscellaneous/gallery/masonry-gallery-with-disc.html',context)
    


@login_required(login_url="/admin-dashboard/login_home")
def hover(request):
    context = {"breadcrumb":{"title":"Image Hover Effects","parent":"Gallery", "child":"Image Hover Effects"}}    
    return render(request,'miscellaneous/gallery/gallery-hover.html',context)
    
#------------------------------------Blog

@login_required(login_url="/admin-dashboard/login_home")
def blog_details(request):  
    context = {"breadcrumb":{"title":"Blog Details","parent":"Blog", "child":"Blog Details"}}    
    return render(request,'miscellaneous/blog/blog.html',context)


@login_required(login_url="/admin-dashboard/login_home")
def blog_single(request):
    context = {"breadcrumb":{"title":"Blog Single","parent":"Blog", "child":"Blog Single"}}    
    return render(request,'miscellaneous/blog/blog-single.html',context)


@login_required(login_url="/admin-dashboard/login_home")
def add_post(request):
    context = {"breadcrumb":{"title":"Add Post","parent":"Blog", "child":"Add Post"}}    
    return render(request,'miscellaneous/blog/add-post.html',context)
    

#---------------------------------job serach

@login_required(login_url="/admin-dashboard/login_home")
def job_cards(request):
    context = {"breadcrumb":{"title":"Cards View","parent":"Job search", "child":"Cards View"}}    
    return render(request,'miscellaneous/job-search/job-cards-view.html',context)
    

@login_required(login_url="/admin-dashboard/login_home")
def job_list(request):
    context = {"breadcrumb":{"title":"List View","parent":"Job search", "child":"List View"}}    
    return render(request,'miscellaneous/job-search/job-list-view.html',context)
    

@login_required(login_url="/admin-dashboard/login_home")
def job_details(request):
    context = {"breadcrumb":{"title":"Job Details","parent":"Job search", "child":"Job Details"}}    
    return render(request,'miscellaneous/job-search/job-details.html',context)
    

@login_required(login_url="/admin-dashboard/login_home")
def apply(request):
    context = {"breadcrumb":{"title":"Apply","parent":"Job search", "child":"Apply"}}    
    return render(request,'miscellaneous/job-search/job-apply.html',context)
    
#------------------------------------Learning

@login_required(login_url="/admin-dashboard/login_home")
def course_list(request):
    context = {"breadcrumb":{"title":"Course List","parent":"Course", "child":"Course List"}}    
    return render(request,'miscellaneous/courses/course-list-view.html',context)
    

@login_required(login_url="/admin-dashboard/login_home")
def course_detailed(request):
    context = {"breadcrumb":{"title":"Course Details","parent":"Course", "child":"Course Details"}}    
    return render(request,'miscellaneous/courses/course-detailed.html',context)
    

#----------------------------------------Maps
@login_required(login_url="/admin-dashboard/login_home")
def data_map(request):
    context = {"breadcrumb":{"title":"Map JS","parent":"Maps", "child":"Map JS"}}    
    return render(request,'miscellaneous/maps/map-js.html',context)
    
   
@login_required(login_url="/admin-dashboard/login_home")
def vector_maps(request):
    context = {"breadcrumb":{"title":"Vector Maps","parent":"Maps", "child":"Vector Maps"}}
    return render(request,'miscellaneous/maps/vector-map.html',context)
    

#------------------------------------Editors
   
@login_required(login_url="/admin-dashboard/login_home")
def quilleditor(request):
    context = {"breadcrumb":{"title":"Quill Editor","parent":"Editors", "child":"Quill Editor"}}    
    return render(request,'miscellaneous/editors/quilleditor.html',context)
    

@login_required(login_url="/admin-dashboard/login_home")
def ckeditor(request):
    context = {"breadcrumb":{"title":"Ck Editor","parent":"Editors", "child":"Ck Editor"}}    
    return render(request,'miscellaneous/editors/ckeditor.html',context)
    
    
@login_required(login_url="/admin-dashboard/login_home")
def ace_code(request):
    context = {"breadcrumb":{"title":"ACE Code Editor","parent":"Editors", "child":"ACE Code Editor"}}    
    return render(request,'miscellaneous/editors/ace-code-editor.html',context) 
    
    
#----------------------------knowledgebase
@login_required(login_url="/admin-dashboard/login_home")
def knowledgebase(request):
    context = {"breadcrumb":{"title":"Knowledgebase","parent":"Knowledgebase", "child":"Knowledgebase"}}    
    return render(request,'miscellaneous/knowledgebase/knowledgebase.html',context)
    
    
#-----------------------------support-ticket
@login_required(login_url="/admin-dashboard/login_home")    
def support_ticket(request):
    context = { "breadcrumb":{"title":"Support ticket","parent":"Support ticket", "child":"Support Ticket"}}
    return render(request,"miscellaneous/support-ticket/support-ticket.html",context)


#------------------------home page client section
from django.views.decorators.csrf import csrf_exempt
def clientBrands(request):
    brands = ClientBrand.objects.all()
    return render (request,'home_content/clientBrand.html', {'brands': brands})



@csrf_exempt
def add_client_brand(request):
    if request.method == "POST" and request.FILES.get('image'):
        image = request.FILES['image']
        ClientBrand.objects.create(image=image)
        return JsonResponse({"status": "success", "message": "Brand added successfully."})
    return JsonResponse({"status": "error", "message": "Image is required."})


@csrf_exempt
def edit_client_brand(request):
    if request.method == "POST":
        brand_id = request.POST.get('id')
        try:
            brand = ClientBrand.objects.get(id=brand_id)
            if 'image' in request.FILES:
                brand.image = request.FILES['image']
                brand.save()
                return JsonResponse({"status": "success", "message": "Brand updated successfully."})
            else:
                return JsonResponse({"status": "error", "message": "No image uploaded."})
        except ClientBrand.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Brand not found."})
    return JsonResponse({"status": "error", "message": "Invalid request."})

@csrf_exempt
def delete_client_brand(request):
    if request.method == "POST":
        data = json.loads(request.body)
        try:
            brand = ClientBrand.objects.get(id=data.get("id"))
            brand.delete()
            return JsonResponse({"status": "success", "message": "Brand deleted."})
        except ClientBrand.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Brand not found."})
        
        
        
def categorybanner(request):
    banners = CategoryBanner.objects.all().order_by('order')
    return render(request,'home_content/categoryBanner.html', {'banners': banners})

def add_category_banner(request):
    if request.method == "POST":
        image = request.FILES.get('image')
        title = request.POST.get('title')
        description = request.POST.get('description')
        button_text = request.POST.get('button_text')
        button_link = request.POST.get('button_link')
        order = request.POST.get('order')

        if not (image and title and description and button_text and button_link and order):
            return JsonResponse({'success': False, 'error': 'All fields are required.'})

        try:
            order = int(order)
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Order must be a number.'})

        banner = CategoryBanner(
            image=image,
            title=title,
            description=description,
            button_text=button_text,
            button_link=button_link,
            order=order
        )
        banner.save()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Only POST allowed.'})


def edit_category_banner(request, banner_id):
    banner = get_object_or_404(CategoryBanner, pk=banner_id)

    if request.method == "POST":
        title = request.POST.get('title')
        description = request.POST.get('description')
        button_text = request.POST.get('button_text')
        button_link = request.POST.get('button_link')
        order = request.POST.get('order')

        if not (title and description and button_text and button_link and order):
            return JsonResponse({'success': False, 'error': 'All fields are required.'})

        try:
            order = int(order)
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Order must be a number.'})

        banner.title = title
        banner.description = description
        banner.button_text = button_text
        banner.button_link = button_link
        banner.order = order

        if 'image' in request.FILES:
            banner.image = request.FILES['image']

        banner.save()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Only POST allowed.'})


def delete_category_banner(request, banner_id):
    if request.method == "POST":
        banner = get_object_or_404(CategoryBanner, pk=banner_id)
        banner.delete()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Only POST allowed.'})



def adBanner(request):
    banners = AdvertisingBanner.objects.all().order_by('order')
    categories = Category.objects.filter(parent_category__isnull=True)
    
    for banner in banners:
        # Get all sub-sub categories (categories with no children)
        sub_sub_categories = []
        for category in banner.categories.all():
            # Check if this category has no children (is a sub-sub category)
            if not Category.objects.filter(parent_category=category).exists():
                sub_sub_categories.append(category.name)
        
        # Join all sub-sub categories with comma
        banner.display_categories = ", ".join(sub_sub_categories) if sub_sub_categories else "No category"
    
    context = {
        'banners': banners,
        'categories': categories
    }
    return render(request, 'home_content/advertisingBanner.html', context)


def add_ad_banner(request):
    if request.method == "POST":
        image = request.FILES.get('image')
        title = request.POST.get('title')
        description = request.POST.get('description')
        button_text = request.POST.get('button_text')
        button_link = request.POST.get('button_link')
        order = request.POST.get('order')
        
        # Get all category IDs from both sets
        category_ids = [
            request.POST.get('category'),
            request.POST.get('sub_category'),
            request.POST.get('sub_sub_category'),
            request.POST.get('category2'),
            request.POST.get('sub_category2'),
            request.POST.get('sub_sub_category2')
        ]

        if not (image and title and description and button_text and button_link and order):
            return JsonResponse({'success': False, 'error': 'All fields are required.'})

        try:
            order = int(order)
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Order must be a number.'})

        try:
            banner = AdvertisingBanner.objects.create(
                image=image,
                title=title,
                description=description,
                button_text=button_text,
                button_link=button_link,
                order=order
            )
            
            # Add all valid categories
            for category_id in category_ids:
                if category_id:  # Only process if not empty
                    try:
                        category = Category.objects.get(id=category_id)
                        banner.categories.add(category)
                    except (Category.DoesNotExist, ValueError):
                        pass
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Only POST allowed.'})


def edit_ad_banner(request, banner_id):
    banner = get_object_or_404(AdvertisingBanner, pk=banner_id)

    if request.method == "POST":
        title = request.POST.get('title')
        description = request.POST.get('description')
        button_text = request.POST.get('button_text')
        button_link = request.POST.get('button_link')
        order = request.POST.get('order')

        if not (title and description and button_text and button_link and order):
            return JsonResponse({'success': False, 'error': 'All fields are required.'})

        try:
            order = int(order)
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Order must be a number.'})

        banner.title = title
        banner.description = description
        banner.button_text = button_text
        banner.button_link = button_link
        banner.order = order

        if 'image' in request.FILES:
            banner.image = request.FILES['image']

        banner.save()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Only POST allowed.'})


def delete_ad_banner(request, banner_id):
    if request.method == "POST":
        banner = get_object_or_404(AdvertisingBanner, pk=banner_id)
        banner.delete()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Only POST allowed.'})


#home page middle section orrfer card

def offerbanner(request):
    banners = OfferBanner.objects.all()
    return render(request, 'home_content/offerBanner.html', {'banners': banners})

def add_offer_banner(request):
    if request.method == "POST":
        image = request.FILES.get('image')
        title = request.POST.get('title')
        subtitle = request.POST.get('subtitle')
        button_text = request.POST.get('button_text')
        button_link = request.POST.get('button_link')

        if not (image and title and button_text and button_link):
            return JsonResponse({'success': False, 'error': 'All fields except subtitle are required.'})

        banner = OfferBanner(
            image=image,
            title=title,
            subtitle=subtitle,
            button_text=button_text,
            button_link=button_link
        )
        banner.save()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Only POST allowed.'})


def edit_offer_banner(request, banner_id):
    banner = get_object_or_404(OfferBanner, pk=banner_id)

    if request.method == "POST":
        title = request.POST.get('title')
        subtitle = request.POST.get('subtitle')
        button_text = request.POST.get('button_text')
        button_link = request.POST.get('button_link')

        if not (title and button_text and button_link):
            return JsonResponse({'success': False, 'error': 'All fields except subtitle are required.'})

        banner.title = title
        banner.subtitle = subtitle
        banner.button_text = button_text
        banner.button_link = button_link

        if 'image' in request.FILES:
            banner.image = request.FILES['image']

        banner.save()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Only POST allowed.'})


def delete_offer_banner(request, banner_id):
    if request.method == "POST":
        banner = get_object_or_404(OfferBanner, pk=banner_id)
        banner.delete()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Only POST allowed.'})
    
    
    
    
    
    
    
    
    
@login_required(login_url="/admin-dashboard/login_home")
def edit_order(request, order_id):
    """Display order edit form"""
    order = get_object_or_404(Order, id=order_id)
    
    # Get all order items through vendor_orders (your actual structure)
    order_items = []
    for vendor_order in order.vendor_orders.all():
        for item in vendor_order.items.all():
            item.total_price = item.final_price * item.quantity
            item.vendor = vendor_order.vendor
            item.vendor_order_id = vendor_order.id
            order_items.append(item)
    
    # Get all products for adding new items (using publish_status instead of is_active)
    available_products = Product.objects.filter(publish_status=1).select_related('seller')  # 4 = Approved
    
    context = {
        "breadcrumb": {"title": "Edit Order", "parent": "Ecommerce", "child": "Edit Order"},
        "order": order,
        "order_items": order_items,
        "available_products": available_products,
    }
    return render(request, "orders/edit-order.html", context)

@login_required(login_url="/admin-dashboard/login_home")
@require_POST
def update_order(request, order_id):
    """Update existing order with modified items"""
    order = get_object_or_404(Order, id=order_id)
    
    try:
        with transaction.atomic():
            # Get the updated items data from form
            items_data = json.loads(request.POST.get('items_data', '[]'))
            
            print(f"Received items_data: {items_data}")  # Debug line
            
            if not items_data:
                messages.error(request, 'No items data received. Please try again.')
                return redirect('edit_order', order_id=order.id)
            
            # Store original total for comparison
            original_total = order.grand_total
            
            # CLEAR existing items but keep the SAME order
            # Delete all existing vendor orders and their items
            for vendor_order in order.vendor_orders.all():
                vendor_order.items.all().delete()
            order.vendor_orders.all().delete()
            
            # Group items by vendor to recreate vendor orders
            vendor_items = {}
            
            for item_data in items_data:
                product_id = item_data['product_id']
                quantity = int(item_data['quantity'])
                
                if quantity <= 0:
                    continue  # Skip items with 0 or negative quantity
                
                try:
                    product = Product.objects.get(id=product_id)
                except Product.DoesNotExist:
                    continue  # Skip if product doesn't exist
                
                vendor = product.seller
                
                if vendor.id not in vendor_items:
                    vendor_items[vendor.id] = {
                        'vendor': vendor,
                        'items': []
                    }
                
                # Use selling_price based on your template
                price = product.selling_price
                
                vendor_items[vendor.id]['items'].append({
                    'product': product,
                    'quantity': quantity,
                    'price': price
                })
            
            # Recreate vendor orders and items for the SAME main order
            total_subtotal = 0
            
            for vendor_id, vendor_data in vendor_items.items():
                # Calculate vendor totals
                vendor_subtotal = 0
                
                # Create OrderVendor (not Order) linked to the SAME main order
                vendor_order = OrderVendor.objects.create(
                    order=order,  # Link to the SAME existing order
                    vendor=vendor_data['vendor'],
                    vendor_status=order.status
                )
                
                # Create order items for this vendor order
                for item_info in vendor_data['items']:
                    order_item = OrderItem.objects.create(
                        vendor_order=vendor_order,  # Link to vendor order
                        product=item_info['product'],
                        quantity=item_info['quantity'],
                        base_price=item_info['price'],
                        final_price=item_info['price']
                    )
                    
                    # Calculate subtotals
                    item_total = item_info['price'] * item_info['quantity']
                    vendor_subtotal += item_total
                    total_subtotal += item_total
                
                # Update vendor order totals
                vendor_order.vendor_subtotal = vendor_subtotal
                vendor_order.vendor_total = vendor_subtotal  # Assuming no vendor-specific discounts
                vendor_order.save()
            
            # UPDATE the SAME order record - don't create new one
            order.subtotal = total_subtotal
            order.grand_total = total_subtotal - (order.discount_total or 0) + (order.shipping_total or 0)
            order.updated_at = timezone.now()  # Update timestamp
            
            # Add admin note about the edit
            admin_note = f"Order edited by {request.user.username} on {timezone.now().strftime('%Y-%m-%d %H:%M')}"
            if hasattr(order, 'admin_notes'):
                if order.admin_notes:
                    order.admin_notes = f"{order.admin_notes}\n{admin_note}"
                else:
                    order.admin_notes = admin_note
            
            # SAVE the updated order (same record, just modified)
            order.save()
            
            print(f"Order updated successfully. New total: {order.grand_total}")  # Debug line
            
            messages.success(request, f'Order #{order.order_number} has been updated successfully! New total: ${order.grand_total:.2f}')
            return redirect('order_details', order_id=order.id)
            
    except Exception as e:
        print(f"Error updating order: {str(e)}")  # Debug line
        messages.error(request, f'Error updating order: {str(e)}')
        return redirect('edit_order', order_id=order.id)

@login_required(login_url="/admin-dashboard/login_home")
@require_POST
def remove_order_item(request, order_id, item_id):
    """AJAX endpoint to remove a specific order item"""
    try:
        order = get_object_or_404(Order, id=order_id)
        
        # Find and remove the item from vendor orders
        item_removed = False
        for vendor_order in order.vendor_orders.all():
            if vendor_order.items.filter(id=item_id).exists():
                vendor_order.items.get(id=item_id).delete()
                item_removed = True
                
                # If vendor order has no more items, remove it
                if not vendor_order.items.exists():
                    vendor_order.delete()
                else:
                    # Recalculate vendor order totals
                    vendor_subtotal = sum(
                        item.final_price * item.quantity 
                        for item in vendor_order.items.all()
                    )
                    vendor_order.vendor_subtotal = vendor_subtotal
                    vendor_order.vendor_total = vendor_subtotal
                    vendor_order.save()
                break
        
        if not item_removed:
            return JsonResponse({'success': False, 'error': 'Item not found'})
        
        # Recalculate main order totals
        order.recalculate_totals()
        
        return JsonResponse({
            'success': True,
            'new_total': float(order.grand_total),
            'new_subtotal': float(order.subtotal)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})





    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    