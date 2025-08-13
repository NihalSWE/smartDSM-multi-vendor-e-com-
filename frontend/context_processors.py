from decimal import Decimal
from django.db.models import Q
from django.utils import timezone
from smart.models import Product, ProductDiscount




# def cart_context(request):
#     cart = request.session.get("cart", {})
#     cart_items = []
#     total_price = Decimal("0.00")  # total payable amount after discounts
#     total_quantity = 0

#     now = timezone.now()

#     for product_id, item in cart.items():
#         try:
#             product = Product.objects.get(pk=product_id)
#         except Product.DoesNotExist:
#             continue

#         price = product.selling_price  # original selling price (Decimal)
#         quantity = item["quantity"]
#         total_quantity += quantity

#         discounts = product.discounts.filter(active=True).filter(
#             (Q(start_date__lte=now) | Q(start_date__isnull=True)) &
#             (Q(end_date__gte=now) | Q(end_date__isnull=True))
#         )

#         if discounts.exists():
#             discount = discounts.first()

#             if discount.discount_type == ProductDiscount.FIXED and discount.discount_price is not None:
#                 discount_amount = discount.discount_price  # amount to subtract from price

#             elif discount.discount_type == ProductDiscount.PERCENT and discount.percentage is not None:
#                 discount_amount = price * (discount.percentage / Decimal("100"))

#             elif discount.discount_type == ProductDiscount.BULK:
#                 if discount.bulk_quantity and quantity >= discount.bulk_quantity:
#                     if discount.bulk_discount_type == ProductDiscount.FIXED and discount.bulk_discount_value:
#                         discount_amount = discount.bulk_discount_value
#                     elif discount.bulk_discount_type == ProductDiscount.PERCENT and discount.bulk_discount_value:
#                         discount_amount = price * (discount.bulk_discount_value / Decimal("100"))
#                     else:
#                         discount_amount = Decimal("0.00")
#                 else:
#                     discount_amount = Decimal("0.00")

#             else:
#                 discount_amount = Decimal("0.00")
#         else:
#             discount_amount = Decimal("0.00")

#         discounted_price = price - discount_amount
#         if discounted_price < 0:
#             discounted_price = Decimal("0.00")

#         subtotal = discounted_price * quantity  # total payable amount for this product line
#         total_price += subtotal

#         cart_items.append({
#             "id": product.id,
#             "slug": product.slug,
#             "name": product.title,
#             "image": product.thumbnail_image.url if product.thumbnail_image else "",
#             "price": price,
#             "discounted_price": discounted_price,
#             "quantity": quantity,
#             "subtotal": subtotal,  # total payable amount per product line
#         })

#     return {
#         "cart_items": cart_items,
#         "cart_count": total_quantity,
#         "cart_total": total_price.quantize(Decimal("0.01")),
#     }


def cart_context(request):
    cart = request.session.get("cart", {})
    cart_items = []
    total_price = Decimal("0.00")  # total payable amount after discounts
    total_quantity = 0
    total_discount = Decimal("0.00")
    total_price_without_discount = Decimal("0.00")

    now = timezone.now()

    for product_id, item in cart.items():
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            continue

        price = product.selling_price  # original selling price (Decimal)
        quantity = item["quantity"]
        total_quantity += quantity

        discounts = product.discounts.filter(active=True).filter(
            (Q(start_date__lte=now) | Q(start_date__isnull=True)) &
            (Q(end_date__gte=now) | Q(end_date__isnull=True))
        )

        if discounts.exists():
            discount = discounts.first()

            if discount.discount_type == ProductDiscount.FIXED and discount.discount_price is not None:
                discount_amount = discount.discount_price  # amount to subtract from price

            elif discount.discount_type == ProductDiscount.PERCENT and discount.percentage is not None:
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

        print('discount price: ', discount_amount)
        discounted_price = price - discount_amount
        if discounted_price < 0:
            discounted_price = Decimal("0.00")

        subtotal = discounted_price * quantity  # total payable amount for this product line
        total_price += subtotal
        
        total_price_without_discount += price

        cart_items.append({
            "id": product.id,
            "slug": product.slug,
            "name": product.title,
            "image": product.thumbnail_image.url if product.thumbnail_image else "",
            "price": price,
            "discounted_price": discounted_price,
            "discount_amount": discount_amount,  # Add this line
            "quantity": quantity,
            "subtotal": subtotal,  # total payable amount per product line
        })

        # Calculate the per-product total discount
        line_discount = discount_amount * quantity
        total_discount += line_discount
        
    shipping_cost = 100
    total_price += shipping_cost
    
    return {
        "cart_items": cart_items,
        "cart_count": total_quantity,
        "cart_total": total_price.quantize(Decimal("0.01")),
        "cart_discount_total": total_discount.quantize(Decimal("0.01")),
        "total_price_without_discount": total_price_without_discount.quantize(Decimal("0.01"))
    }