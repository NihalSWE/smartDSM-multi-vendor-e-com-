from django.db import models, transaction
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager, Group, Permission
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from .utils.slug_utils import generate_unique_slug
from uuid import uuid4
from django.utils import timezone
from django.db.models import F, Q
from django.core.files.storage import default_storage
from io import BytesIO
from django.core.files.base import ContentFile
from decimal import Decimal
from PIL import Image
import os
import uuid







class Package(models.Model):
    PACKAGE_TYPE_CHOICES = [
        (0, 'Free'),
        (1, 'Paid'),
    ]
    
    package_id = models.CharField(max_length=10, unique=True, editable=False)
    name = models.CharField(max_length=100)
    package_type = models.PositiveSmallIntegerField(choices=PACKAGE_TYPE_CHOICES, default=0)
    description = models.TextField(blank=True, null=True)
    max_products = models.PositiveIntegerField(default=0)
    can_use_variants = models.BooleanField(default=False)
    can_create_discounts = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    duration_days = models.PositiveIntegerField(default=30)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk and not self.package_id:
            # Only generate package_id on creation
            existing_ids = Package.objects.exclude(package_id='').values_list('package_id', flat=True)
            numeric_ids = [int(pid) for pid in existing_ids if pid.isdigit()]
            next_id = max(numeric_ids, default=0) + 1
            self.package_id = str(next_id).zfill(3)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.package_id} - {self.name}"
    
    
    
class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, user_id=None, user_type=3, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        if not username:
            raise ValueError("Username is required")
        if not password:
            raise ValueError("Password is required")

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            username=username,
            user_id=user_id or f"user_{uuid.uuid4().hex[:8]}",
            user_type=user_type,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, user_id=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 0)

        # Let create_user handle user_id generation
        return self.create_user(
            email=email,
            username=username,
            password=password,
            user_id=user_id,  # Can be None
            **extra_fields
        )


class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = (
        (0, 'Root'),
        (1, 'Vendor'),
        (2, 'Staff'),
        (3, 'Client'),
    )

    STATUS_CHOICES = (
        (0, 'Inactive'),
        (1, 'Active'),
        (2, 'Suspended'),
    )

    user_id = models.CharField(unique=True, max_length=15, blank=True, null=True)
    username = models.CharField(unique=True, max_length=150, blank=True, null=True)
    email = models.EmailField(unique=True, max_length=100)
    phone_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    address = models.CharField(max_length=250, blank=True, null=True)
    city = models.CharField(max_length=250, blank=True, null=True)
    state = models.CharField(max_length=250, blank=True, null=True)
    postal_code = models.CharField(max_length=50, blank=True, null=True)

    package = models.ForeignKey('Package', on_delete=models.SET_NULL, null=True, blank=True)

    user_type = models.IntegerField(choices=USER_TYPE_CHOICES, default=2)
    user_status = models.IntegerField(choices=STATUS_CHOICES, default=1)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)



    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def save(self, *args, **kwargs):
        # Generate user_id only if it's not already set
        if not self.user_id:
            # You can customize the prefix and length as needed
            self.user_id = 'USR-' + str(uuid.uuid4())[:8].upper() # Example: USR-ABCDEF12

        # if not self.is_superuser:
        #     if self.package:
        #         if self.package.package_type == 0:
        #             self.user_type = 3  # Client
        #         else:
        #             self.user_type = 1  # Vendor
        #     else:
        #         self.user_type = 2 # Default to Staff if no package is assigned
                
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    hire_date = models.DateField(null=True, blank=True)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    profile_picture = models.URLField(blank=True, null=True)
    linkedin_profile = models.URLField(blank=True, null=True)
    github_profile = models.URLField(blank=True, null=True)
    biography = models.TextField(blank=True, null=True)
    timezone = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.user.username
    
    

class VendorContactInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='contact_info')
    business_logo = models.ImageField(upload_to='vendor/logos/', blank=True, null=True)
    business_name = models.CharField(max_length=255)
    business_address = models.TextField()
    phone_number = models.CharField(max_length=20)
    postal_code = models.CharField(max_length=20)
    business_email = models.EmailField()
    contact_person_name = models.CharField(max_length=255)
    contact_person_phone = models.CharField(max_length=20)

    def __str__(self):
        return self.business_name



class VendorCompanyOverview(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company_overview')
    business_details = models.TextField()
    establishment_date = models.DateField()
    business_type = models.CharField(max_length=100)
    is_licensed = models.BooleanField(default=False)
    is_insured = models.BooleanField(default=False)
    tax_certificate = models.FileField(upload_to='vendor_documents/tax_certificates/', blank=True, null=True)
    trade_licence = models.FileField(upload_to='vendor_documents/trade_licences/', blank=True, null=True)
    additional_info = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Overview of {self.user.username}"



class VendorFinancialInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='financial_info')
    bank_name = models.CharField(max_length=255)
    card_last4 = models.CharField(max_length=4)
    expiration_date = models.CharField(max_length=7)  # MM/YYYY
    shift_code = models.CharField(max_length=50)
    # cvv is excluded for security reasons

    def __str__(self):
        return f"Financial Info of {self.user.username}"



class VendorVerification(models.Model):
    STATUS_CHOICES = [
        (0, 'Pending'),
        (1, 'Approved'),
        (2, 'Rejected'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)

    # Change to IntegerField ✅
    status = models.IntegerField(
        choices=STATUS_CHOICES,
        default=0,  # Default to Pending
        help_text="Current verification status of the vendor."
    )

    def __str__(self):
        return f"{self.user.username} - {'Verified' if self.is_verified else 'Not Verified'}"
    
    def save_model(self, request, obj, form, change):
        """
        Overrides the save_model method to automatically update
        is_verified and verified_at based on the status field.
        """
        # Get the original object from the database if it's an existing instance
        original_obj = None
        if obj.pk:
            original_obj = VendorVerification.objects.get(pk=obj.pk)

        # ✅ Now obj.status is an integer, compare with int
        if obj.status == 1:  # Approved
            obj.is_verified = True
            if original_obj is None or original_obj.status != 1:
                obj.verified_at = timezone.now()
        else:
            obj.is_verified = False
            obj.verified_at = None

        super().save_model(request, obj, form, change)  # Save the object



class VendorReview(models.Model):
    vendor = models.ForeignKey(User, limit_choices_to={'user_type': 1}, on_delete=models.CASCADE, related_name='reviews')
    client = models.ForeignKey(User, limit_choices_to={'user_type': 3}, on_delete=models.CASCADE)
    rating = models.IntegerField()  # 1-5
    review = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client.username} reviewed {self.vendor.username}"
    


class CategoryType(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # slug
        if not self.slug:
            self.slug = generate_unique_slug(self, Product, 'slug')
            
        super().save(*args, **kwargs)



class Category(models.Model):
    STATUS_CHOICES = (
        (0, 'Inactive'),
        (1, 'Active'),
    )

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    category_type = models.ForeignKey(CategoryType, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    
    parent_category = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        related_name='subcategories',
        blank=True,
        null=True
    )
    
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)

    # 🔹 Image fields
    banner = models.ImageField(upload_to='categories/banners/', blank=True, null=True)  # 1244x257
    thumbnail_small = models.ImageField(upload_to='categories/thumbnails/', blank=True, null=True)  # 400x400
    icon = models.ImageField(upload_to='categories/icons/', blank=True, null=True)  # small icon

    position = models.PositiveIntegerField(default=0)
    code = models.PositiveIntegerField(unique=True, editable=False)  # Will auto-increment starting from 10

    meta_key = models.CharField(max_length=255, blank=True, null=True)
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:  # 🔹 always ensure slug exists
            self.slug = generate_unique_slug(self, Category, 'slug')
        elif self.pk:
            old_instance = Category.objects.get(pk=self.pk)
            if old_instance.name != self.name:
                self.slug = generate_unique_slug(self, Category, 'slug')

        if not self.code:
            last = Category.objects.order_by('-code').first()
            self.code = (last.code + 1) if last else 10

        super().save(*args, **kwargs)

        # 🔹 Resize images after saving
        self.resize_image(self.banner, (1244, 257))
        self.resize_image(self.thumbnail_small, (400, 400))


    def resize_image(self, image_field, size):
        """Resize uploaded image to exact size (if provided)."""
        if image_field and os.path.isfile(image_field.path):
            img = Image.open(image_field.path)
            img = img.resize(size, Image.Resampling.LANCZOS)
            img.save(image_field.path)

    def __str__(self):
        return self.name
    @property
    def has_children(self):
        return self.subcategories.filter(status=1).exists()
        


# ——————————————————————————————————————————————
# Tags & Shipping Classes
# ——————————————————————————————————————————————

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, Tag, 'slug')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ShippingClass(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


# ——————————————————————————————————————————————
# Core Product Models
# ——————————————————————————————————————————————

class ProductQuerySet(models.QuerySet):
    def approved(self):
        return self.filter(publish_status=4)  # Approved

    def pending(self):
        return self.filter(publish_status=2)  # Pending

    def rejected(self):
        return self.filter(publish_status=3)  # Rejected

    def published(self):
        return self.filter(publish_status=1)  # Published
    
    
    
class Product(models.Model):
    PUBLISH_STATUS = (
        (0, 'Draft'),
        (1, 'Published'),
        (2, 'Pending'),
        (3, 'Rejected'),
        (4, 'Approved'),
    )

    sku                 = models.CharField(max_length=50, unique=True)
    title               = models.CharField(max_length=255)
    model               = models.CharField(max_length=255, blank=True, null=True)
    slug                = models.SlugField(max_length=255, unique=True)
    description         = models.TextField(blank=True, null=True)
    short_description   = models.TextField(max_length=200,blank=True, null=True)
    
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products', help_text="Who is selling this item")

    thumbnail_image     = models.ImageField(upload_to='products/thumbnails/')
    thumbnail_small = models.ImageField(upload_to='products/thumbnails/small/', blank=True, null=True)
    # gallery of additional images
    # see ProductImage below

    code                = models.CharField(max_length=20, unique=True, editable=False)
    buy_price           = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    selling_price       = models.DecimalField(max_digits=10, decimal_places=2)

    # category hierarchy (Category model assumed self-referential)
    category            = models.ForeignKey('Category', related_name='products', on_delete=models.PROTECT)
    parent_category            = models.ForeignKey('Category', related_name='parent_products', on_delete=models.PROTECT, blank=True, null=True)
    sub_category        = models.ForeignKey('Category', related_name='sub_products', on_delete=models.PROTECT, blank=True, null=True)
    sub_sub_category    = models.ForeignKey('Category', related_name='sub_sub_products', on_delete=models.PROTECT, blank=True, null=True)

    tags                = models.ManyToManyField(Tag, blank=True)

    # inventory & availability
    stock_availability  = models.BooleanField(default=True)
    low_stock_level     = models.PositiveIntegerField(default=5)
    stock_quantity      = models.PositiveIntegerField(default=0)
    restock_date        = models.DateField(blank=True, null=True)
    preorder_quantity   = models.PositiveIntegerField(default=0)
    is_digital_product  = models.BooleanField(default=False)

    # SEO
    meta_title          = models.CharField(max_length=255, blank=True, null=True)
    meta_keywords       = models.CharField(max_length=255, blank=True, null=True)
    meta_description    = models.TextField(blank=True, null=True)

    # shipping
    weight              = models.DecimalField(max_digits=8, decimal_places=3, blank=True, null=True)
    length              = models.DecimalField(max_digits=8, decimal_places=3, blank=True, null=True)
    width               = models.DecimalField(max_digits=8, decimal_places=3, blank=True, null=True)
    height              = models.DecimalField(max_digits=8, decimal_places=3, blank=True, null=True)
    shipping_class      = models.ForeignKey(ShippingClass, on_delete=models.SET_NULL, blank=True, null=True)

    # publish controls
    publish_status      = models.IntegerField(choices=PUBLISH_STATUS, default=2)
    rejection_reason    = models.TextField(blank=True, null=True, help_text="Reason for rejection (required if rejected)")
    is_new              = models.BooleanField(default=True, help_text="True if product is newly uploaded or updated")
    publish_date        = models.DateTimeField(blank=True, null=True)

    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)
    
    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Slug + product code logic
        if self.pk:
            old_instance = Product.objects.get(pk=self.pk)
            
            # check if anything important changed → mark as new
            tracked_fields = ["title", "description", "short_description", "selling_price", "thumbnail_image"]
            for field in tracked_fields:
                if getattr(old_instance, field) != getattr(self, field):
                    self.is_new = True
                    break
            else:
                self.is_new = False
                
            if old_instance.title != self.title:
                self.slug = generate_unique_slug(self, Product, 'slug', 'title')
        else:
            self.slug = generate_unique_slug(self, Product, 'slug', 'title')
            self.is_new = True

        if not self.code:
            last = Product.objects.order_by('-code').first()
            self.code = str(int(last.code) + 1) if last and last.code.isdigit() else '10'

        super().save(*args, **kwargs)

        # === Thumbnail optimization ===
        if self.thumbnail_image:
            img_path = self.thumbnail_image.path
            img = Image.open(img_path)

            # generate small (250x250) thumbnail
            min_side = min(img.width, img.height)
            left = (img.width - min_side) / 2
            top = (img.height - min_side) / 2
            right = (img.width + min_side) / 2
            bottom = (img.height + min_side) / 2
            img = img.crop((left, top, right, bottom))
            img = img.resize((250, 250), Image.LANCZOS)

            # Save in memory → file
            buffer = BytesIO()
            img.save(buffer, format="JPEG", optimize=True, quality=70)
            file_name = f"{self.pk}_thumb250.jpg"
            self.thumbnail_small.save(file_name, ContentFile(buffer.getvalue()), save=False)

            buffer.close()
            super().save(update_fields=["thumbnail_small"])

    def __str__(self):
        return self.title
    
    def get_discounted_price(self):
        # If there’s an active discount with a discount_price, subtract it
        discount = self.discounts.filter(active=True, discount_price__isnull=False).first()
        
        if discount:
            final_price = self.selling_price - discount.discount_price
        else:
            final_price = self.selling_price

        return round(final_price, 2)    


class ProductImage(models.Model):
    product = models.ForeignKey(
        'Product',
        related_name='images',
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to='products/images/')
    image_small = models.ImageField(upload_to='products/images/small/', blank=True, null=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"{self.product.title} Image #{self.position}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Save first to get the file path

        img_path = self.image.path
        img = Image.open(img_path)

        max_size = (800, 800)

        # If bigger than 800x800 → crop & resize
        if img.width > 800 or img.height > 800:
            # First, crop to square (center crop)
            min_side = min(img.width, img.height)
            left = (img.width - min_side) / 2
            top = (img.height - min_side) / 2
            right = (img.width + min_side) / 2
            bottom = (img.height + min_side) / 2
            img = img.crop((left, top, right, bottom))

            # Then resize to 800x800
            img = img.resize(max_size, Image.LANCZOS)
            img.save(img_path)
            
            # === Create small version (250x250) ===
            small_img = img.copy()
            small_img = small_img.resize((250, 250), Image.LANCZOS)
            buffer = BytesIO()
            small_img.save(buffer, format='JPEG', quality=70)
            self.image_small.save(f"{self.pk}_small.jpg", ContentFile(buffer.getvalue()), save=False)
            
            super().save(update_fields=['image_small'])
    
    
# example best seller, new arrival
class ProductLabel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.ImageField(upload_to='labels/icons/', blank=True, null=True)  # Optional
    color = models.CharField(max_length=7, blank=True, null=True)  # e.g. "#ff6600"

    def save(self, *args, **kwargs):
        if self.pk:
            old_instance = Category.objects.get(pk=self.pk)
            if old_instance.name != self.name:
                self.slug = generate_unique_slug(self, Category, 'slug')
        else:
            self.slug = generate_unique_slug(self, Category, 'slug')

        if not self.code:
            last = Category.objects.order_by('-code').first()
            self.code = (last.code + 1) if last else 10

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    

class ProductLabelRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='label_requests')
    label = models.ForeignKey(ProductLabel, on_delete=models.CASCADE)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='label_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    admin_comment = models.TextField(blank=True, null=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('product', 'label')

    def __str__(self):
        return f"{self.product.title} - {self.label.name} ({self.status})"


# ——————————————————————————————————————————————
# Discounts
# ——————————————————————————————————————————————

class ProductDiscount(models.Model):
    FIXED      = 'fixed'
    PERCENT    = 'percentage'
    BOGO       = 'bogo'
    BULK       = 'bulk'
    TYPE_CHOICES = (
        (FIXED, 'Fixed Price'),
        (PERCENT, 'Percentage'),
        (BOGO, 'Buy-One-Get-One'),
        (BULK, 'Bulk/Volume'),
    )

    product           = models.ForeignKey(Product, related_name='discounts', on_delete=models.CASCADE)
    discount_type     = models.CharField(max_length=20, choices=TYPE_CHOICES)

    # common
    active            = models.BooleanField(default=True)
    start_date        = models.DateTimeField(blank=True, null=True)
    end_date          = models.DateTimeField(blank=True, null=True)

    # for FIXED
    discount_price    = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # for PERCENT
    percentage        = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    # for BOGO
    free_product      = models.ForeignKey(Product, blank=True, null=True, related_name='bogo_free_for', on_delete=models.SET_NULL)
    min_price         = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    max_price         = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # for BULK
    bulk_quantity     = models.PositiveIntegerField(blank=True, null=True)
    bulk_discount_type = models.CharField(max_length=20, choices=((FIXED,'Fixed'),(PERCENT,'Percent')), blank=True, null=True)
    bulk_discount_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"{self.get_discount_type_display()} for {self.product.title}"


# ——————————————————————————————————————————————
# Variations & Options
# ——————————————————————————————————————————————

class ProductVariationType(models.Model):
    name        = models.CharField(max_length=50)
    product     = models.ForeignKey(Product, related_name='variation_types', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('name', 'product')

    def __str__(self):
        return f"{self.name} ({self.product.title})"


class ProductVariationOption(models.Model):
    variation_type  = models.ForeignKey(ProductVariationType, related_name='options', on_delete=models.CASCADE)
    value           = models.CharField(max_length=50)  # e.g. “Red”, “XL”, “2kg”
    price_modifier  = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # optional

    class Meta:
        unique_together = ('variation_type', 'value')

    def __str__(self):
        return f"{self.variation_type.name}: {self.value}"
    
    
class ProductVariant(models.Model):
    product     = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    sku         = models.CharField(max_length=60, unique=True)
    price       = models.DecimalField(max_digits=10, decimal_places=2)
    # override stock if needed per‐variant
    stock_quantity    = models.PositiveIntegerField(default=0)
    is_active         = models.BooleanField(default=True)

    class Meta:
        unique_together = (('product', 'sku'),)
        ordering = ['sku']

    def __str__(self):
        return f"{self.product.title} [{self.sku}]"


class VariantOptionSelection(models.Model):
    variant         = models.ForeignKey(ProductVariant, related_name='selections', on_delete=models.CASCADE)
    variation_type  = models.ForeignKey(ProductVariationType, on_delete=models.CASCADE)
    option          = models.ForeignKey(ProductVariationOption, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('variant', 'variation_type'),)

    def __str__(self):
        return f"{self.variant.sku}: {self.variation_type.name} = {self.option.value}"
    
    
class Slider(models.Model):
    STATUS_CHOICES = (
        (0, 'Inactive'),
        (1, 'Active'),
    )
    
    ALIGNMENT_CHOICES = (
        (0, 'Left'),
        (1, 'Right'),
    )

    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='sliders/images/', blank=True, null=True)
    background_image = models.ImageField(upload_to='sliders/backgrounds/')

    paragraph = models.TextField(blank=True, null=True)
    paragraph_color = models.CharField(max_length=7, blank=True, null=True, help_text="Hex color (e.g. #000000)")

    heading_h3 = models.CharField(max_length=255, blank=True, null=True)
    heading_h3_color = models.CharField(max_length=7, blank=True, null=True, help_text="Hex color (e.g. #ff0000)")

    heading_h5 = models.CharField(max_length=255, blank=True, null=True)
    heading_h5_color = models.CharField(max_length=7, blank=True, null=True, help_text="Hex color (e.g. #333333)")

    button_link = models.URLField(blank=True, null=True)

    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    position = models.PositiveIntegerField(default=0)
    
    text_alignment = models.IntegerField(choices=ALIGNMENT_CHOICES, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position', 'name']

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Wrap in a transaction so our shifts and save happen atomically.
        with transaction.atomic():
            # Are we creating a brand-new slider?
            if self._state.adding:
                # If no explicit position was set or position < 1, append at end.
                if not self.position or self.position < 1:
                    max_pos = Slider.objects.aggregate(max=models.Max('position'))['max'] or 0
                    self.position = max_pos + 1
                else:
                    # shift existing sliders at >= this position up by 1
                    Slider.objects.filter(position__gte=self.position).update(position=F('position') + 1)
            else:
                # We're updating an existing slider.
                # Fetch its previous position from the DB.
                old = Slider.objects.get(pk=self.pk)
                old_pos = old.position
                new_pos = self.position

                # If position wasn’t changed, do nothing special.
                if new_pos and new_pos != old_pos:
                    # Temporarily “vacate” the old slot
                    # shift those between old_pos+1 and infinity down by 1
                    Slider.objects.filter(position__gt=old_pos).update(position=F('position') - 1)

                    # Now insert at new_pos: shift up everyone at >= new_pos
                    Slider.objects.filter(position__gte=new_pos).update(position=F('position') + 1)

            # Finally save ourselves into our newly-cleared slot
            super().save(*args, **kwargs)
            
            
class ProductReview(models.Model):
    RATING_CHOICES = [
        (1, "Very Poor"),
        (2, "Not That Bad"),
        (3, "Average"),
        (4, "Good"),
        (5, "Perfect"),
    ]
    
    product = models.ForeignKey('Product', related_name='reviews', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    text = models.TextField(verbose_name="Review Text")  # <-- renamed to 'text' for clarity
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.product.name} ({self.rating})"
            
            

class contactPageHeader(models.Model):
    page_slug = models.SlugField(unique=True, help_text="e.g., contact-us, become-a-vendor")
    title = models.CharField(max_length=255)
    background_image = models.ImageField(upload_to='media/contact_page_headers/')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.page_slug} - {self.title}"




class contactFAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.question
    
class ContactMessage(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} ({self.email})"


# Conatct page branch locations
class ContactLocation(models.Model):
    city = models.CharField(max_length=100)
    address = models.TextField()
    email = models.EmailField(max_length=100,blank=True,null=True)
    number = models.CharField(max_length=20,blank=True,null=True)  # Mandatory
    image = models.ImageField(upload_to='media/contact_locations/', null=True, blank=True)

    def __str__(self):
        return self.city

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            img = Image.open(self.image.path)
            img = img.convert('RGB')  # Ensure it's in a valid format
            img = img.resize((160, 108), Image.LANCZOS)
            img.save(self.image.path)



#--Become a vendor--
class vendorregisterPageHeader(models.Model):
    page_slug = models.SlugField(unique=True, help_text="e.g., contact-us, become-a-vendor")
    title = models.CharField(max_length=255)
    background_image = models.ImageField(upload_to='media/vendor_register_page_headers/')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.page_slug} - {self.title}"
    
    
    
#--Blog List Header---
class BlogListPageHeader(models.Model):
    page_slug = models.SlugField(unique=True, help_text="e.g., contact-us, become-a-vendor")
    title = models.CharField(max_length=255)
    background_image = models.ImageField(upload_to='media/Blog-List-page_headers/')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.page_slug} - {self.title}"
    
    
#--Blog List Header---
class BlogPageHeader(models.Model):
    page_slug = models.SlugField(unique=True, help_text="e.g., contact-us, become-a-vendor")
    title = models.CharField(max_length=255)
    background_image = models.ImageField(upload_to='media/Blog-page_headers/')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.page_slug} - {self.title}"
    
    

#--AboutUs page header

class AboutusPageHeader(models.Model):
    page_slug = models.SlugField(unique=True, help_text="e.g., contact-us, become-a-vendor")
    title = models.CharField(max_length=255)
    background_image = models.ImageField(upload_to='media/AboutUs-page_headers/')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.page_slug} - {self.title}"
 
 
 
class AboutPageContent(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to="about/")
    button_text = models.CharField(max_length=100, blank=True, null=True)
    button_url = models.CharField(max_length=25,blank=True, null=True)

    def __str__(self):
        return self.title       
    
#--AboutUs page header

class FaqsPageHeader(models.Model):
    page_slug = models.SlugField(unique=True, help_text="e.g., contact-us, become-a-vendor")
    title = models.CharField(max_length=255)
    background_image = models.ImageField(upload_to='media/Faq-page_headers/')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.page_slug} - {self.title}"
    
    
#--wishlist page header

class WishlistPageHeader(models.Model):
    page_slug = models.SlugField(unique=True, help_text="e.g., contact-us, become-a-vendor")
    title = models.CharField(max_length=255)
    background_image = models.ImageField(upload_to='media/Wishlist-page_headers/')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.page_slug} - {self.title}"
    
    
#home page clients section
class ClientBrand(models.Model):
    image = models.ImageField(upload_to='media/brands/')

    def __str__(self):
        return f"Brand {self.id}"
    
#home page category cards
# models.py
from django.db import models

class CategoryBanner(models.Model):
    image = models.ImageField(upload_to='media/category_banners/')
    title = models.CharField(max_length=200,blank=True,null=True)
    description = models.TextField(max_length=500,blank=True,null=True)
    button_text = models.CharField(max_length=50, default="Shop Now")
    button_link = models.CharField(max_length=50,default="#")
    order = models.PositiveIntegerField(unique=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.order}. {self.title}"


#home page Advertising cards
class AdvertisingBanner(models.Model):
    categories = models.ManyToManyField(Category, related_name='advertising_banners', blank=True)
    title = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(max_length=500, blank=True, null=True)
    image = models.ImageField(upload_to='media/advertising-banners/')
    button_text = models.CharField(max_length=50, default='Shop Now')
    button_link = models.CharField(max_length=50, default='#')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title} ({self.order})"

#home page middle orrfer card
class OfferBanner(models.Model):
    title = models.CharField(max_length=100)
    subtitle = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='media/offer-banners/')
    button_text = models.CharField(max_length=50, default='Shop Now')
    button_link = models.CharField(max_length=255, default='#')  # ← Changed from URLField to CharField

    def __str__(self):
        return self.title
    

class District(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Thana(models.Model):
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name="thanas")
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('district', 'name')
        ordering = ['name']

    def __str__(self):
        return f"{self.name}, {self.district.name}"


class Address(models.Model):
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='addresses',
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=50, default="Home")  # "Home", "Office", etc.
    district = models.CharField(max_length=100, blank=True, null=True)
    thana = models.CharField(max_length=100, blank=True, null=True)
    street_address = models.TextField()
    postal_code = models.CharField(max_length=10, blank=True, null=True)
    phone_number = models.CharField(max_length=20)
    city = models.CharField(max_length=50, blank=True, null=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} - {self.street_address}, {self.thana}, {self.district}"

# ----------------------------------
# Order Models
# ----------------------------------

class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        (0, 'Pending'),
        (1, 'Processing'),
        (2, 'Shipped'),
        (3, 'Completed'),
        (4, 'Cancelled'),
        (5, 'Refunded'),
    ]

    PAYMENT_STATUS_CHOICES = [
        (0, 'Due'),
        (1, 'Paid'),
        (2, 'Partially Paid'),
        (3, 'Failed'),
        (4, 'Refunded'),
    ]

    PAYMENT_METHOD_CHOICES = [
        (0, 'Cash on Delivery'),
        (1, 'Credit/Debit Card'),
        (2, 'bKash'),
        (3, 'Nagad'),
        (4, 'SSL'),
    ]

    order_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='orders',
        limit_choices_to={'user_type': 3},
        null=True,     # allow null for guest users
        blank=True,    # allow blank in forms/admin
    )


    status = models.PositiveSmallIntegerField(choices=ORDER_STATUS_CHOICES, default=0)
    payment_status = models.PositiveSmallIntegerField(choices=PAYMENT_STATUS_CHOICES, default=0)
    payment_method = models.PositiveSmallIntegerField(choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    shipping_address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='shipping_orders')
    billing_address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='billing_orders', blank=True, null=True)

    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = "ORD-" + str(uuid4())[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_number}"
        
        
        
    def recalculate_totals(self):
        """Recalculate order totals based on current items through vendor_orders"""
        subtotal = 0
        
        # Calculate subtotal from all vendor orders and their items
        for vendor_order in self.vendor_orders.all():
            vendor_subtotal = 0
            for item in vendor_order.items.all():
                item_total = item.final_price * item.quantity
                subtotal += item_total
                vendor_subtotal += item_total
            
            # Update vendor order totals
            vendor_order.vendor_subtotal = vendor_subtotal
            vendor_order.vendor_total = vendor_subtotal
            vendor_order.save()
        
        self.subtotal = subtotal
        
        # Recalculate grand total (keeping existing discount and shipping)
        discount = self.discount_total or 0
        shipping = self.shipping_total or 0
        
        self.grand_total = subtotal - discount + shipping
        self.updated_at = timezone.now()
        
        self.save()
        
        return self.grand_total

    def add_admin_note(self, note, user):
        """Add an admin note to the order"""
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
        new_note = f"[{timestamp}] {user.username}: {note}"
        
        if hasattr(self, 'admin_notes') and self.admin_notes:
            self.admin_notes = f"{self.admin_notes}\n{new_note}"
        else:
            self.admin_notes = new_note
        
        self.save()

    def get_total_items_count(self):
        """Get total number of items in the order through vendor_orders"""
        total = 0
        for vendor_order in self.vendor_orders.all():
            total += vendor_order.items.aggregate(
                total=models.Sum('quantity')
            )['total'] or 0
        return total


class OrderVendor(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='vendor_orders')
    vendor = models.ForeignKey('User', on_delete=models.CASCADE, limit_choices_to={'user_type': 1}, related_name='vendor_orders')

    vendor_subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vendor_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vendor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vendor_status = models.PositiveSmallIntegerField(choices=Order.ORDER_STATUS_CHOICES, default=0)

    shipped_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.vendor.username} - {self.order.order_number}"


class OrderItem(models.Model):
    vendor_order = models.ForeignKey(OrderVendor, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.PROTECT, related_name='order_items')
    variation_option = models.ForeignKey('ProductVariationOption', on_delete=models.SET_NULL, blank=True, null=True, related_name='order_items')

    quantity = models.PositiveIntegerField(default=1)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_applied = models.ForeignKey('ProductDiscount', on_delete=models.SET_NULL, blank=True, null=True)

    def get_total_price(self):
        return self.final_price * Decimal(self.quantity)

    def __str__(self):
        return f"{self.product.title} x {self.quantity}"
    

class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.PositiveSmallIntegerField(choices=Order.ORDER_STATUS_CHOICES)
    new_status = models.PositiveSmallIntegerField(choices=Order.ORDER_STATUS_CHOICES)
    changed_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True)
    note = models.TextField(blank=True, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f"Order {self.order.order_number} changed from {self.get_old_status_display()} to {self.get_new_status_display()}"



class OrderPayment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.PositiveSmallIntegerField(choices=Order.PAYMENT_METHOD_CHOICES)
    paid_at = models.DateTimeField(blank=True, null=True)
    is_successful = models.BooleanField(default=False)
    raw_response = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Payment for {self.order.order_number} - {'Success' if self.is_successful else 'Failed'}"



#order notification
class OrderNotification(models.Model):
    order = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='notification')
    is_viewed = models.BooleanField(default=False)
    viewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    viewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for Order #{self.order.order_number}"


# STEP 2: Add this signal at the bottom of your models.py or create signals.py

        
        
        
        
        
        
        
        
        
#order notification
class OrderNotification(models.Model):
    order = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='notification')
    is_viewed = models.BooleanField(default=False)
    viewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    viewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for Order #{self.order.order_number}"
        
        
        
        
#vendor order list 
from django.conf import settings
class VendorOrderNotice(models.Model):
    """
    Tracks which OrderItem has been explicitly notified to its vendor.
    Vendors only see items from this table.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="notices")
    vendor_order = models.ForeignKey(OrderVendor, on_delete=models.CASCADE, related_name="notices")
    item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name="notices")

    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="vendor_notices"
    )

    notified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="sent_vendor_notices"
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("item", "vendor")  # avoid duplicate notifications

    def __str__(self):
        return f"Notice: {self.item} → {self.vendor}"
    
    
    
class VendorOrderNotification(models.Model):
    vendor_order = models.OneToOneField(
        'OrderVendor',
        on_delete=models.CASCADE,
        related_name='notification'
    )
    is_viewed = models.BooleanField(default=False)
    viewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    viewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for VendorOrder #{self.vendor_order.id} ({self.vendor_order.vendor.username})"
        
        
        
        
#delivery charge
class DeliveryType(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    description = models.TextField(blank=True, null=True)
    vendor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delivery_types')
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            
            # Make slug unique for this vendor
            while DeliveryType.objects.filter(
                slug=slug, 
                vendor=self.vendor
            ).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.vendor.username}"

    class Meta:
        unique_together = ('name', 'vendor')
        ordering = ['-created_at']


class DeliveryCharge(models.Model):
    delivery_type = models.ForeignKey(
        DeliveryType, 
        on_delete=models.CASCADE,
        related_name='charges'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    vendor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='delivery_charges'
    )
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.delivery_type.name} - ৳{self.amount}"

    class Meta:
        unique_together = ('delivery_type', 'vendor')
        ordering = ['-created_at']
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
