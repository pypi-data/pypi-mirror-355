from django.utils.translation import gettext as _
from netbox.forms import NetBoxModelFilterSetForm, NetBoxModelForm
from utilities.forms.fields import ColorField, SlugField, TagFilterField
from utilities.forms.rendering import FieldSet

from inventory_monitor.models import AssetType


class AssetTypeForm(NetBoxModelForm):
    slug = SlugField()

    fieldsets = (FieldSet("name", "slug", "color", "description", "tags"),)

    class Meta:
        model = AssetType
        fields = [
            "name",
            "slug",
            "color",
            "description",
            "tags",
        ]


class AssetTypeFilterForm(NetBoxModelFilterSetForm):
    model = AssetType
    fieldsets = (
        FieldSet("q", "filter_id", "tag"),
        FieldSet("color", name=_("Attributes")),
    )
    tag = TagFilterField(model)

    color = ColorField(label=_("Color"), required=False)
