from django import template
from django.contrib.contenttypes.models import ContentType

register = template.Library()


@register.filter
def get_status(obj, status_type):
    """
    Gets the status for the given object and status type
    Example: {{ record|get_status:'warranty' }} calls record.get_warranty_status()
    """
    method_name = f"get_{status_type}_status"
    if hasattr(obj, method_name):
        return getattr(obj, method_name)()
    return None


@register.filter
def get_content_type_param(obj):
    """
    Returns the appropriate query parameter name for the given object.
    Example: For a Device object, returns 'device'
    """
    if obj is None:
        return None

    # Get the model name in lowercase
    content_type = ContentType.objects.get_for_model(obj)
    model_name = content_type.model.lower()

    # You can customize this mapping if needed
    param_mapping = {
        # 'custommodelname': 'custom_param_name',
    }

    # Return the mapped param name or the model name by default
    return param_mapping.get(model_name, model_name)
