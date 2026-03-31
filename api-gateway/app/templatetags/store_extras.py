from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def vnd(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        amount = Decimal("0")

    amount = amount.quantize(Decimal("1"))
    normalized = f"{int(amount):,}".replace(",", ".")
    return f"{normalized} VND"
