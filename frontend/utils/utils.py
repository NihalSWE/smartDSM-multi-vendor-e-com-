from django.db.models import Q
from django.utils.timezone import now
from decimal import Decimal
import random
from smart.models import *


def get_discounted_price(product):
    """
    Returns (final_price, discount_value, discount_type) considering active discounts
    that are within date range.
    """
    current_time = now()

    active_discount = (
        product.discounts
        .filter(active=True)
        .filter(
            Q(start_date__isnull=True) | Q(start_date__lte=current_time),
            Q(end_date__isnull=True) | Q(end_date__gte=current_time)
        )
        .order_by('-start_date')
        .first()
    )

    if not active_discount:
        return (product.selling_price, None, None)

    if active_discount.discount_type == ProductDiscount.FIXED:
        discount_value = product.selling_price - active_discount.discount_price
        return (active_discount.discount_price, discount_value, 'fixed')

    elif active_discount.discount_type == ProductDiscount.PERCENT:
        discount_value = (product.selling_price * active_discount.percentage) / Decimal('100')
        return (product.selling_price - discount_value, discount_value, 'percent')

    # For BOGO / BULK — just show original price for now
    return (product.selling_price, None, active_discount.discount_type)



def get_new_arrivals(limit=10):
    products = []

    # Step 1: Get 1 product from each parent category first
    parent_cats = Category.objects.filter(parent_category__isnull=True, status=1).order_by('position')

    for cat in parent_cats:
        if len(products) >= limit:
            break
        product = Product.objects.filter(
            category=cat,
            publish_status=1
        ).order_by('-created_at').first()
        if product:
            products.append(product)

    # Step 2: If still not enough, get from subcategories and sub-subcategories
    if len(products) < limit:
        other_cats = Category.objects.filter(parent_category__isnull=False, status=1).order_by('position')
        for cat in other_cats:
            if len(products) >= limit:
                break
            product = Product.objects.filter(
                category=cat,
                publish_status=1
            ).order_by('-created_at').first()
            if product and product not in products:
                products.append(product)

    # Step 3: If still not enough, fill from newest products overall
    if len(products) < limit:
        latest_products = Product.objects.filter(
            publish_status=1
        ).order_by('-created_at')[:limit]
        for product in latest_products:
            if len(products) >= limit:
                break
            if product not in products:
                products.append(product)

    return products