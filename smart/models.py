from django.db import models, transaction
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager, Group, Permission
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from .utils.slug_utils import generate_unique_slug
from django.utils import timezone
from django.db.models import F, Q
from django.core.files.storage import default_storage
from io import BytesIO
from django.core.files.base import ContentFile
from decimal import Decimal
from PIL import Image
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

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def save(self, *args, **kwargs):
        # Generate user_id only if it's not already set
        if not self.user_id:
            # You can customize the prefix and length as needed
            self.user_id = 'USR-' + str(uuid.uuid4())[:8].upper() # Example: USR-ABCDEF12

        if not self.is_superuser:
            if self.package:
                if self.package.package_type == 0:
                    self.user_type = 3  # Client
                else:
                    self.user_type = 1  # Vendor
            else:
                self.user_type = 2 # Default to Staff if no package is assigned
                
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
        ('0', 'Pending'),
        ('1', 'Approved'),
        ('2', 'Rejected'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=1, # Max length of the choice key (e.g., '0', '1', '2')
        choices=STATUS_CHOICES,
        default='0', # Set a default status, e.g., 'Pending'
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
        # This is important to check if the status has actually changed
        original_obj = None
        if obj.pk:
            original_obj = VendorVerification.objects.get(pk=obj.pk)

        # Check if the status field has changed to 'Approved'
        if obj.status == '1': # '1' is the database value for 'Approved'
            obj.is_verified = True
            
            if original_obj is None or original_obj.status != '1':
                obj.verified_at = timezone.now()
        else:
            obj.is_verified = False
            obj.verified_at = None

        super().save_model(request, obj, form, change) # Call the parent save_model to save the object



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
    slug = models.SlugField(max_length=255, unique=True, blank=True)
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
    slug                = models.SlugField(max_length=255, unique=True)
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
        return self.title


class ProductImage(models.Model):
    product     = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image       = models.ImageField(upload_to='products/images/')
    position    = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"{self.product.title} Image #{self.position}"
    
    
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
