from decimal import Decimal
from django.db.models import Q
from django.utils import timezone
from smart.models import *


def cart_context(request):
    cart = request.session.get("cart", {})
    cart_items = []
    total_price_without_discount = Decimal("0.00")  # subtotal before discount
    total_discount = Decimal("0.00")
    total_quantity = 0

    now = timezone.now()
    
    has_own_products = False  # <--- NEW FLAG

    for product_id, item in cart.items():
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            continue

        price = product.selling_price  # original selling price (Decimal)
        quantity = item["quantity"]
        total_quantity += quantity
        
        # Check if product belongs to the logged-in user
        if request.user.is_authenticated and product.seller == request.user:
            has_own_products = True

        # --- find discount amount ---
        discounts = product.discounts.filter(active=True).filter(
            (Q(start_date__lte=now) | Q(start_date__isnull=True)) &
            (Q(end_date__gte=now) | Q(end_date__isnull=True))
        )

        if discounts.exists():
            discount = discounts.first()

            if discount.discount_type == ProductDiscount.FIXED and discount.discount_price:
                discount_amount = discount.discount_price
            elif discount.discount_type == ProductDiscount.PERCENT and discount.percentage:
                discount_amount = price * (discount.percentage / Decimal("100"))
            elif discount.discount_type == ProductDiscount.BULK:
                if discount.bulk_quantity and quantity >= discount.bulk_quantity:
                    if discount.bulk_discount_type == ProductDiscount.FIXED and discount.bulk_discount_value:
                        discount_amount = discount.bulk_discount_value
                    elif discount.bulk_discount_type == ProductDiscount.PERCENT and discount.bulk_discount_value:
                        discount_amount = price * (discount.bulk_discount_value / Decimal("100"))
                    else:
                        discount_amount = Decimal("0.00")
                else:
                    discount_amount = Decimal("0.00")
            else:
                discount_amount = Decimal("0.00")
        else:
            discount_amount = Decimal("0.00")

        discounted_price = price - discount_amount
        if discounted_price < 0:
            discounted_price = Decimal("0.00")

        line_subtotal = discounted_price * quantity
        line_discount = discount_amount * quantity

        # --- accumulate totals ---
        total_price_without_discount += price * quantity
        total_discount += line_discount

        cart_items.append({
            "id": product.id,
            "slug": product.slug,
            "name": product.title,
            "image": product.thumbnail_image.url if product.thumbnail_image else "",
            "price": price,
            "discounted_price": discounted_price,
            "discount_amount": discount_amount,
            "quantity": quantity,
            "subtotal": line_subtotal,
        })

    # shipping_cost = Decimal("100.00")
    grand_total = (total_price_without_discount - total_discount)
    
    print('has_own_products: ', has_own_products)

    return {
        "cart_items": cart_items,
        "cart_count": total_quantity,

        # match template variable names
        "subtotal": total_price_without_discount.quantize(Decimal("0.01")),
        "discount_total": total_discount.quantize(Decimal("0.01")),
        "grand_total": grand_total.quantize(Decimal("0.01")),
        "has_own_products": has_own_products,
    }
    
    
    
def categories_context(request):
    """
    Context processor to provide hierarchical categories for navigation menu
    """
    try:
        main_categories = Category.objects.filter(
            status=1,
            parent_category__isnull=True
        ).prefetch_related(
            'subcategories__subcategories'
        ).order_by('position', 'name')

        default_icons = {
            'fashion': 'w-icon-tshirt2',
            'clothing': 'w-icon-tshirt2',
            'home': 'w-icon-home',
            'garden': 'w-icon-home',
            'electronics': 'w-icon-electronics',
            'furniture': 'w-icon-furniture',
            'beauty': 'w-icon-heartbeat',
            'health': 'w-icon-heartbeat',
            'gift': 'w-icon-gift',
            'toys': 'w-icon-gamepad',
            'games': 'w-icon-gamepad',
            'cooking': 'w-icon-ice-cream',
            'kitchen': 'w-icon-ice-cream',
            'phone': 'w-icon-ios',
            'mobile': 'w-icon-ios',
            'camera': 'w-icon-camera',
            'photo': 'w-icon-camera',
            'accessories': 'w-icon-ruby',
            'jewelry': 'w-icon-ruby',
        }

        def get_icon(category):
            if category.icon:
                return {'type': 'image', 'url': category.icon.url}
            for keyword, icon_class in default_icons.items():
                if keyword in category.name.lower():
                    return {'type': 'class', 'class': icon_class}
            return {'type': 'class', 'class': 'w-icon-category'}

        structured = []

        for category in main_categories:
            subcats = category.subcategories.filter(status=1).order_by('position', 'name')
            category_data = {
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
                'icon': get_icon(category),
                'banner': category.banner.url if category.banner else None,
                'subcategories': []
            }

            for subcat in subcats:
                children = subcat.subcategories.filter(status=1).order_by('position', 'name')
                category_data['subcategories'].append({
                    'id': subcat.id,
                    'name': subcat.name,
                    'slug': subcat.slug,
                    'children': [
                        {
                            'id': child.id,
                            'name': child.name,
                            'slug': child.slug
                        } for child in children
                    ]
                })

            structured.append(category_data)

        return {'navigation_categories': structured}

    except Exception as e:
        print("Error in categories_context:", e)
        return {'navigation_categories': []}
