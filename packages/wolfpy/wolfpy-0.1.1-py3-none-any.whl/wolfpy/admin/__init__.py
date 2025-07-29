"""
WolfPy Admin Interface

Django-style admin interface for WolfPy applications.
"""

from ..core.admin import AdminSite, ModelAdmin, AdminUser, site, register

__all__ = [
    'AdminSite',
    'ModelAdmin', 
    'AdminUser',
    'site',
    'register'
]
