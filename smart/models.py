from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager, Group, Permission
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from .utils.slug_utils import generate_unique_slug
from django.utils import timezone
from django.core.files.storage import default_storage
from io import BytesIO
from django.core.files.base import ContentFile
from decimal import Decimal
import uuid





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
    address = models.CharField(max_length=250, blank=True, null=True)
    city = models.CharField(max_length=250, blank=True, null=True)
    state = models.CharField(max_length=250, blank=True, null=True)
    postal_code = models.CharField(max_length=50, blank=True, null=True)
    user_type = models.IntegerField(choices=USER_TYPE_CHOICES, default=2)
    user_status = models.IntegerField(choices=STATUS_CHOICES, default=1)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    # REQUIRED_FIELDS = ['user_id', 'username', 'phone_number']

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
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {'Verified' if self.is_verified else 'Not Verified'}"



class VendorReview(models.Model):
    vendor = models.ForeignKey(User, limit_choices_to={'user_type': 1}, on_delete=models.CASCADE, related_name='reviews')
    client = models.ForeignKey(User, limit_choices_to={'user_type': 3}, on_delete=models.CASCADE)
    rating = models.IntegerField()  # 1-5
    review = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client.username} reviewed {self.vendor.username}"
    
    

class Category(models.Model):
    STATUS_CHOICES = (
        (0, 'Inactive'),
        (1, 'Active'),
    )

    name = models.CharField(max_length=255, unique=True)
    slug_name = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    
    parent_category = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        related_name='subcategories',
        blank=True,
        null=True
    )
    
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    image = models.ImageField(upload_to='categories/images/', blank=True, null=True)
    icon = models.ImageField(upload_to='categories/icons/', blank=True, null=True)
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
        if not self.slug_name:
            self.slug_name = generate_unique_slug(self, Category, 'slug_name')

        if not self.code:
            last = Category.objects.order_by('-code').first()
            self.code = (last.code + 1) if last else 10

        super().save(*args, **kwargs)
        


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

class Product(models.Model):
    PUBLISH_STATUS = (
        (0, 'Draft'),
        (1, 'Published'),
    )

    sku                 = models.CharField(max_length=50, unique=True)
    title               = models.CharField(max_length=255)
    slug                = models.SlugField(max_length=255, unique=True, blank=True)
    description         = models.TextField(blank=True, null=True)
    
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products', help_text="Who is selling this item")

    thumbnail_image     = models.ImageField(upload_to='products/thumbnails/')
    # gallery of additional images
    # see ProductImage below

    code                = models.CharField(max_length=20, unique=True, editable=False)
    buy_price           = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    selling_price       = models.DecimalField(max_digits=10, decimal_places=2)

    # category hierarchy (Category model assumed self-referential)
    category            = models.ForeignKey('Category', related_name='products', on_delete=models.PROTECT)
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
    publish_status      = models.IntegerField(choices=PUBLISH_STATUS, default=0)
    publish_date        = models.DateTimeField(blank=True, null=True)

    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # slug
        if not self.slug:
            self.slug = generate_unique_slug(self, Product, 'slug')
        # code: e.g. “P-0001”, you could customize format
        if not self.code:
            last = Product.objects.order_by('-id').first()
            idx = (last.id + 1) if last else 1
            self.code = f"P-{idx:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ProductImage(models.Model):
    product     = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image       = models.ImageField(upload_to='products/images/')
    position    = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"{self.product.title} Image #{self.position}"


# ——————————————————————————————————————————————
# Discounts
# ——————————————————————————————————————————————

class Discount(models.Model):
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

class VariationType(models.Model):
    name        = models.CharField(max_length=50)
    product     = models.ForeignKey(Product, related_name='variation_types', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('name', 'product')

    def __str__(self):
        return f"{self.name} ({self.product.title})"


class VariationOption(models.Model):
    variation_type  = models.ForeignKey(VariationType, related_name='options', on_delete=models.CASCADE)
    value           = models.CharField(max_length=50)  # e.g. “Red”, “XL”, “2kg”
    price_modifier  = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # optional

    class Meta:
        unique_together = ('variation_type', 'value')

    def __str__(self):
        return f"{self.variation_type.name}: {self.value}"