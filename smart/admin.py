from django.contrib import admin
from .models import *







# Register the Package model (from previous)
@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = (
        'package_id',
        'name',
        'package_type',  # Add package_type here
        'price',
        'duration_days',
        'max_products',
        'created_at'
    )
    search_fields = ('name', 'package_id')
    list_filter = (
        'package_type',  # Add package_type to list_filter
        'can_use_variants',
        'can_create_discounts'
    )
    readonly_fields = ('package_id', 'created_at')
    ordering = ('package_id',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'package_type', 'description', 'price', 'duration_days')
        }),
        ('Features', {
            'fields': ('max_products', 'can_use_variants', 'can_create_discounts')
        }),
    )

# Register the User model (from previous)
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username', 'email', 'user_type', 'user_status', 'is_active', 'is_staff', 'package')
    search_fields = ('username', 'email', 'user_id', 'phone_number')
    list_filter = ('user_type', 'user_status', 'is_active', 'is_staff', 'package')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('username', 'user_id', 'first_name', 'last_name', 'phone_number', 'address', 'city', 'state', 'postal_code')}),
        ('Permissions & Status', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('User Type & Package', {'fields': ('user_type', 'user_status', 'package')}),
        ('Important dates', {'fields': ('last_login',)}), # <--- Corrected line: ('last_login',)
    )
    readonly_fields = ('user_id', 'last_login')
    ordering = ('email',)


# Register the UserProfile model (from previous)
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_of_birth', 'gender', 'city', 'country', 'job_title')
    search_fields = ('user__username', 'user__email', 'city', 'country', 'job_title')
    list_filter = ('gender', 'country')
    fieldsets = (
        (None, {'fields': ('user',)}),
        ('Personal Details', {'fields': ('date_of_birth', 'gender', 'biography', 'profile_picture')}),
        ('Contact & Location', {'fields': ('address', 'city', 'state', 'postal_code', 'country', 'timezone')}),
        ('Professional Details', {'fields': ('hire_date', 'job_title', 'skills', 'linkedin_profile', 'github_profile')}),
    )

# Register the VendorContactInfo model (from previous)
@admin.register(VendorContactInfo)
class VendorContactInfoAdmin(admin.ModelAdmin):
    list_display = ('user', 'business_name', 'business_email', 'phone_number', 'contact_person_name')
    search_fields = ('user__username', 'business_name', 'business_email', 'phone_number')
    raw_id_fields = ('user',)
    fieldsets = (
        (None, {'fields': ('user', 'business_logo', 'business_name')}),
        ('Contact Information', {'fields': ('business_address', 'phone_number', 'postal_code', 'business_email')}),
        ('Contact Person', {'fields': ('contact_person_name', 'contact_person_phone')}),
    )

# Register the VendorCompanyOverview model (from previous)
@admin.register(VendorCompanyOverview)
class VendorCompanyOverviewAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'business_type',
        'establishment_date',
        'is_licensed',
        'is_insured',
        'tax_certificate',  # Added this field
        'trade_licence'     # Added this field
    )
    search_fields = ('user__username', 'business_type', 'business_details')
    list_filter = ('is_licensed', 'is_insured', 'business_type')
    raw_id_fields = ('user',)
    fieldsets = (
        (None, {'fields': ('user',)}),
        ('Company Details', {'fields': ('business_details', 'establishment_date', 'business_type')}),
        ('Compliance', {'fields': ('is_licensed', 'is_insured')}),
        # New section for documents
        ('Company Documents', {'fields': ('tax_certificate', 'trade_licence')}), # Added these fields
        ('Additional Information', {'fields': ('additional_info',)}),
    )

# Register the VendorFinancialInfo model (from previous)
@admin.register(VendorFinancialInfo)
class VendorFinancialInfoAdmin(admin.ModelAdmin):
    list_display = ('user', 'bank_name', 'card_last4', 'expiration_date')
    search_fields = ('user__username', 'bank_name', 'card_last4')
    raw_id_fields = ('user',)
    fieldsets = (
        (None, {'fields': ('user', 'bank_name')}),
        ('Card Details', {'fields': ('card_last4', 'expiration_date', 'shift_code')}),
    )


# Register the VendorVerification model (from previous)
@admin.register(VendorVerification)
class VendorVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'is_verified', 'verified_at', 'rejection_reason') # Added 'status' here
    search_fields = ('user__username', 'status',) # You might want to search by status too
    list_filter = ('status', 'is_verified',) # Added 'status' to filters
    readonly_fields = ('verified_at',) # Keep 'verified_at' as readonly
    raw_id_fields = ('user',)

    fieldsets = (
        (None, {
            'fields': ('user', 'status', 'is_verified')
        }),
        ('Verification Details', {
            'fields': ('verified_at', 'rejection_reason'),
            'classes': ('collapse',)
        }),
    )


# Register the VendorReview model (from previous)
@admin.register(VendorReview)
class VendorReviewAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'client', 'rating', 'created_at')
    search_fields = ('vendor__username', 'client__username', 'review')
    list_filter = ('rating', 'created_at')
    raw_id_fields = ('vendor', 'client')
    readonly_fields = ('created_at',)


# Register the Category model (from previous)
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'parent_category', 'status', 'position', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug', 'description')
    list_filter = ('status', 'parent_category')
    readonly_fields = ('code', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'description', 'parent_category')}),
        ('Status & Display', {'fields': ('status', 'image', 'icon', 'position')}),
        ('SEO Information', {'fields': ('meta_key', 'meta_title', 'meta_description')}),
        ('System Info', {'fields': ('code', 'created_at', 'updated_at')}),
    )
    ordering = ('position', 'name')
    
from django.utils.safestring import mark_safe
@admin.register(AdvertisingBanner)
class AdvertisingBannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'button_text', 'button_link', 'get_categories', 'preview_image')
    list_editable = ('order',)
    search_fields = ('title', 'description')
    exclude = ('categories',)  # <-- hides the field from the form

    def get_categories(self, obj):
        return ", ".join([cat.name for cat in obj.categories.all()])
    get_categories.short_description = "Categories"

    def preview_image(self, obj):
        if obj.image:
            return mark_safe(f"<img src='{obj.image.url}' width='100' height='auto' />")
        return "-"
    preview_image.short_description = "Image Preview"

# -----------------------------------------------------------------------------
# New Models from your request
# -----------------------------------------------------------------------------

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ShippingClass)
class ShippingClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


class ProductImageInline(admin.TabularInline):
    """
    Inline for ProductImage to manage multiple images directly from the Product admin.
    """
    model = ProductImage
    extra = 1 # Number of empty forms to display
    fields = ('image', 'position')


class ProductVariationTypeInline(admin.TabularInline):
    """
    Inline for ProductVariationType.
    """
    model = ProductVariationType
    extra = 1
    fields = ('name',)


class ProductVariationOptionInline(admin.TabularInline):
    """
    Inline for ProductVariationOption.
    Can be used with ProductVariationTypeAdmin if needed.
    """
    model = ProductVariationOption
    extra = 1
    fields = ('value', 'price_modifier')


class VariantOptionSelectionInline(admin.TabularInline):
    """
    Inline for VariantOptionSelection.
    """
    model = VariantOptionSelection
    extra = 1
    fields = ('variation_type', 'option')
    # If you want to limit choices for variation_type and option, you'd need
    # to override get_formset or formfield_for_foreignkey here,
    # but that can get complex depending on your exact logic.


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'sku', 'seller', 'category', 'selling_price', 'stock_quantity',
        'publish_status', 'is_digital_product', 'created_at'
    )
    list_filter = (
        'publish_status', 'stock_availability', 'is_digital_product',
        'category', 'sub_category', 'sub_sub_category', 'seller', 'shipping_class'
    )
    search_fields = ('title', 'sku', 'description', 'code', 'seller__username')
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('seller',) # Use raw_id_fields for ForeignKey to User
    filter_horizontal = ('tags',) # For ManyToMany field

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'sku', 'description', 'seller', 'thumbnail_image')
        }),
        ('Pricing & Inventory', {
            'fields': ('buy_price', 'selling_price', 'stock_availability',
                       'low_stock_level', 'stock_quantity', 'restock_date',
                       'preorder_quantity', 'is_digital_product')
        }),
        ('Categorization', {
            'fields': ('category', 'sub_category', 'sub_sub_category', 'tags')
        }),
        ('Shipping Details', {
            'fields': ('weight', 'length', 'width', 'height', 'shipping_class')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_keywords', 'meta_description')
        }),
        ('Publishing', {
            'fields': ('publish_status', 'publish_date', 'code')
        }),
    )
    readonly_fields = ('code', 'created_at', 'updated_at')
    inlines = [ProductImageInline] # Add inline for product images
    # Add inlines for variations if you want to manage them directly from Product:
    # ProductVariationTypeInline, ProductVariantInline (requires custom logic to link options to variants)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image', 'position')
    list_filter = ('product',)
    search_fields = ('product__title',)
    raw_id_fields = ('product',)


@admin.register(ProductLabel)
class ProductLabelAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ProductLabelRequest)
class ProductLabelRequestAdmin(admin.ModelAdmin):
    list_display = ('product', 'label', 'requested_by', 'status', 'requested_at', 'reviewed_at')
    list_filter = ('status', 'label', 'requested_at')
    search_fields = ('product__title', 'label__name', 'requested_by__username', 'admin_comment')
    raw_id_fields = ('product', 'label', 'requested_by')
    readonly_fields = ('requested_at',)
    fieldsets = (
        (None, {'fields': ('product', 'label', 'requested_by')}),
        ('Review Status', {'fields': ('status', 'admin_comment', 'reviewed_at')}),
    )


@admin.register(ProductDiscount)
class ProductDiscountAdmin(admin.ModelAdmin):
    list_display = ('product', 'discount_type', 'active', 'start_date', 'end_date', 'percentage', 'discount_price')
    list_filter = ('discount_type', 'active', 'start_date', 'end_date')
    search_fields = ('product__title',)
    raw_id_fields = ('product', 'free_product')
    fieldsets = (
        (None, {'fields': ('product', 'discount_type', 'active', ('start_date', 'end_date'))}),
        ('Fixed/Percentage Discount', {'fields': ('discount_price', 'percentage'), 'classes': ('collapse',)}),
        ('Buy-One-Get-One (BOGO)', {'fields': ('free_product', 'min_price', 'max_price'), 'classes': ('collapse',)}),
        ('Bulk/Volume Discount', {'fields': ('bulk_quantity', 'bulk_discount_type', 'bulk_discount_value'), 'classes': ('collapse',)}),
    )


@admin.register(ProductVariationType)
class ProductVariationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'product')
    search_fields = ('name', 'product__title')
    list_filter = ('product',)
    raw_id_fields = ('product',)
    inlines = [ProductVariationOptionInline] # Allow managing options directly


@admin.register(ProductVariationOption)
class ProductVariationOptionAdmin(admin.ModelAdmin):
    list_display = ('variation_type', 'value', 'price_modifier')
    search_fields = ('value', 'variation_type__name', 'variation_type__product__title')
    list_filter = ('variation_type',)
    raw_id_fields = ('variation_type',)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'sku', 'price', 'stock_quantity', 'is_active')
    search_fields = ('sku', 'product__title')
    list_filter = ('is_active', 'product')
    raw_id_fields = ('product',)
    inlines = [VariantOptionSelectionInline] # Link variant to its specific option selections


@admin.register(VariantOptionSelection)
class VariantOptionSelectionAdmin(admin.ModelAdmin):
    list_display = ('variant', 'variation_type', 'option')
    search_fields = ('variant__sku', 'variation_type__name', 'option__value')
    list_filter = ('variation_type', 'option')
    raw_id_fields = ('variant', 'variation_type', 'option')


@admin.register(Slider)
class SliderAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'position', 'text_alignment', 'created_at')
    list_filter = ('status', 'text_alignment')
    search_fields = ('name', 'paragraph', 'heading_h3', 'heading_h5')
    fieldsets = (
        (None, {'fields': ('name', 'image', 'background_image')}),
        ('Content', {'fields': ('paragraph', 'paragraph_color', 'heading_h3', 'heading_h3_color', 'heading_h5', 'heading_h5_color')}),
        ('Action & Display', {'fields': ('button_link', 'status', 'position', 'text_alignment')}),
        ('Timestamps', {'fields': ('created_at',), 'classes': ('collapse',)}) # Collapse timestamps
    )
    readonly_fields = ('created_at',)
    ordering = ('position',)
