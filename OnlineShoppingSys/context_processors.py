"""Custom template context processors."""


def is_vendor(request):
    """Add is_vendor to template context - True when user is in Vendor group."""
    if request.user.is_authenticated:
        return {'is_vendor': request.user.groups.filter(name='Vendor').exists()}
    return {'is_vendor': False}
