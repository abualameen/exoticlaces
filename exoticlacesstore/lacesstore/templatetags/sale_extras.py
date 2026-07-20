# lacesstore/templatetags/sale_extras.py
from django import template
from django.utils import timezone
from decimal import Decimal

register = template.Library()


@register.filter
def multiply(value, arg):
    """Multiply two numbers"""
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except:
        return 0


@register.filter
def subtract(value, arg):
    """Subtract two numbers"""
    try:
        return Decimal(str(value)) - Decimal(str(arg))
    except:
        return value


@register.filter
def percentage(value, arg):
    """Calculate percentage"""
    try:
        return Decimal(str(value)) * (Decimal(str(arg)) / 100)
    except:
        return 0