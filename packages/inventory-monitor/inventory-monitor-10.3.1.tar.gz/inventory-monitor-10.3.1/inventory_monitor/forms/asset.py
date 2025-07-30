# Django imports
# Third-party imports
# NetBox imports
from dcim.models import Device, Location, Module, Rack, Site
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext as _
from netbox.forms import (
    NetBoxModelBulkEditForm,
    NetBoxModelFilterSetForm,
    NetBoxModelForm,
)
from utilities.forms import add_blank_choice
from utilities.forms.fields import (
    CommentField,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    TagFilterField,
)
from utilities.forms.rendering import FieldSet, TabbedGroups
from utilities.forms.widgets.datetime import DatePicker

# Local application imports
from inventory_monitor.models import ABRA, Asset, AssetType, Contract
from inventory_monitor.models.asset import (
    ASSIGNED_OBJECT_MODELS_QUERY,
    AssignmentStatusChoices,
    LifecycleStatusChoices,
)


class AssetForm(NetBoxModelForm):
    """
    Form for creating and editing Asset objects
    """

    #
    # Field definitions
    #

    # Identification fields
    name = forms.CharField(
        required=False,
        label="Name",
        widget=forms.TextInput(attrs={"placeholder": "Name"}),
    )
    serial = forms.CharField(
        required=True,
        label="Serial",
        widget=forms.TextInput(attrs={"placeholder": "Serial"}),
    )
    partnumber = forms.CharField(
        required=False,
        label="Part Number",
    )

    # Type and classification
    type = DynamicModelChoiceField(queryset=AssetType.objects.all(), required=False, label="Type")

    # Status fields are defined in the model

    # Assignment fields - these represent the GenericForeignKey options
    site = DynamicModelChoiceField(
        queryset=Site.objects.all(),
        required=False,
        label="Site",
        selector=True,
    )
    location = DynamicModelChoiceField(
        queryset=Location.objects.all(),
        required=False,
        label="Location",
        selector=True,
    )
    rack = DynamicModelChoiceField(
        queryset=Rack.objects.all(),
        required=False,
        label="Rack",
        selector=True,
    )
    device = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        required=False,
        label="Device",
        selector=True,
    )
    module = DynamicModelChoiceField(
        queryset=Module.objects.all(),
        required=False,
        label="Module",
        selector=True,
    )

    # Related object fields
    order_contract = DynamicModelChoiceField(
        queryset=Contract.objects.all(),
        required=False,
        label="Order Contract",
    )
    # Additional information fields
    project = forms.CharField(
        required=False,
        label="Project",
    )
    vendor = forms.CharField(
        required=False,
        label="Vendor",
    )
    quantity = forms.IntegerField(required=True, label="Items", initial=1, min_value=1)
    price = forms.DecimalField(
        required=True,
        label="Price",
        initial=0,
        min_value=0,
        decimal_places=2,
    )

    # Warranty information
    warranty_start = forms.DateField(required=False, label=("Warranty Start"), widget=DatePicker())
    warranty_end = forms.DateField(
        required=False,
        label=("Warranty End"),
        widget=DatePicker(),
    )

    # Metadata fields
    comments = CommentField(label="Comments")

    #
    # Form layout definition
    #
    fieldsets = (
        # Basic asset information
        FieldSet(
            "partnumber",
            "serial",
            "name",
            "type",
            "project",
            "price",
            "vendor",
            "quantity",
            name=_("Asset"),
        ),
        # Status fields
        FieldSet("assignment_status", name=_("Assignment Status")),
        FieldSet("lifecycle_status", name=_("Lifecycle Status")),
        # Assignment options in tabbed interface
        FieldSet(
            TabbedGroups(
                FieldSet("site", name=_("Site")),
                FieldSet("location", name=_("Location")),
                FieldSet("rack", name=_("Rack")),
                FieldSet("device", name=_("Device")),
                FieldSet("module", name=_("Module")),
            ),
            name=_("Component Assignment"),
        ),
        # Related objects
        FieldSet(
            "order_contract",
            name=_("Order Contract"),
        ),
        FieldSet("warranty_start", "warranty_end", name=_("Dates")),
        # Metadata
        FieldSet("tags", name=_("Misc")),
    )

    class Meta:
        model = Asset
        fields = (
            # Identification fields
            "partnumber",
            "serial",
            "name",
            # Type and classification
            "type",
            # Status fields
            "lifecycle_status",
            "assignment_status",
            # Assignment fields
            "site",
            "location",
            "rack",
            "device",
            "module",
            # Related objects
            "order_contract",
            # Additional information
            "project",
            "vendor",
            "quantity",
            "price",
            # Warranty information
            "warranty_start",
            "warranty_end",
            # Metadata
            "comments",
            "tags",
        )

    def __init__(self, *args, **kwargs):
        """
        Override initialization to handle assigned object properly.
        Sets initial values for assigned objects based on instance or passed parameters.
        """
        instance = kwargs.get("instance")
        initial = kwargs.get("initial", {}).copy()
        assigned_object_type = initial.get("assigned_object_type")
        assigned_object_id = initial.get("assigned_object_id")

        if instance:
            # When editing: set the initial value for assigned_object selection
            for assigned_object_model in ContentType.objects.filter(ASSIGNED_OBJECT_MODELS_QUERY):
                if type(instance.assigned_object) is assigned_object_model.model_class():
                    initial[assigned_object_model.model] = instance.assigned_object
                    break
        elif assigned_object_type and assigned_object_id:
            # When adding the Asset from an assigned_object page
            if (
                content_type := ContentType.objects.filter(ASSIGNED_OBJECT_MODELS_QUERY)
                .filter(pk=assigned_object_type)
                .first()
            ):
                if assigned_object := content_type.model_class().objects.filter(pk=assigned_object_id).first():
                    initial[content_type.model] = assigned_object

        kwargs["initial"] = initial
        super().__init__(*args, **kwargs)

    def clean(self):
        """
        Custom validation to ensure only one assigned object is selected.
        Sets the assigned_object property based on the selected field.
        """
        super().clean()

        # Handle object assignment - check that only one is selected
        selected_objects = [
            field
            for field in (
                "site",
                "location",
                "rack",
                "device",
                "module",
            )
            if self.cleaned_data[field]
        ]

        if len(selected_objects) > 1:
            raise forms.ValidationError(_("An Asset can only be assigned to a single object."))
        elif selected_objects:
            self.instance.assigned_object = self.cleaned_data[selected_objects[0]]
        else:
            self.instance.assigned_object = None


class AssetFilterForm(NetBoxModelFilterSetForm):
    """
    Filter form for Asset objects, used in list views
    """

    model = Asset

    #
    # Form layout definition
    #
    fieldsets = (
        # Basic search options
        FieldSet("q", "filter_id", "tag", name=_("Misc")),
        # Status fields
        FieldSet("assignment_status", name=_("Assignment Status")),
        FieldSet("lifecycle_status", name=_("Lifecycle Status")),
        # Related objects for filtering
        FieldSet(
            "order_contract",
            "abra_assets",
            "abra_inventory_number__ic",
            name=_("Related Objects"),
        ),
        # Date range filters
        FieldSet(
            "warranty_start",
            "warranty_start__gte",
            "warranty_start__lte",
            "warranty_end",
            "warranty_end__gte",
            "warranty_end__lte",
            name=_("Warranty Dates"),
        ),
        # Asset information filters
        FieldSet(
            "partnumber",
            "serial",
            "name",
            "type_id",
            "project",
            "vendor",
            name=_("Asset Details"),
        ),
        # Numeric range filters
        FieldSet("quantity", "quantity__gte", "quantity__lte", name=_("Quantity")),
        FieldSet("price", "price__gte", "price__lte", name=_("Price")),
        FieldSet("has_abra_assets", name=_("ABRA Assets")),
    )

    #
    # Field definitions
    #

    # Basic search fields
    tag = TagFilterField(model)

    # Identification filters
    name = forms.CharField(required=False)
    serial = forms.CharField(required=False)
    partnumber = forms.CharField(required=False)
    abra_inventory_number__ic = forms.CharField(
        required=False, label="ABRA Asset Number", help_text="Filter by ABRA inventory number"
    )

    # Status filters
    assignment_status = forms.ChoiceField(choices=add_blank_choice(AssignmentStatusChoices), required=False)

    lifecycle_status = forms.ChoiceField(choices=add_blank_choice(LifecycleStatusChoices), required=False)

    # Type filter
    type_id = DynamicModelMultipleChoiceField(queryset=AssetType.objects.all(), required=False, label=_("Type"))

    # Related object filters
    order_contract = DynamicModelMultipleChoiceField(
        queryset=Contract.objects.all(), required=False, label=_("Order Contract")
    )
    abra_assets = DynamicModelMultipleChoiceField(queryset=ABRA.objects.all(), required=False, label=_("ABRA"))

    # Additional information filters
    project = forms.CharField(
        required=False,
        label="Project",
    )
    vendor = forms.CharField(
        required=False,
        label="Vendor",
    )

    # Quantity filters (exact and range)
    quantity = forms.IntegerField(required=False, label="Items")
    quantity__gte = forms.IntegerField(required=False, label=("Items: From"))
    quantity__lte = forms.IntegerField(required=False, label=("Items: Till"))

    # Price filters (exact and range)
    price = forms.DecimalField(required=False)
    price__gte = forms.DecimalField(
        required=False,
        label=("Price: From"),
    )
    price__lte = forms.DecimalField(
        required=False,
        label=("Price: Till"),
    )

    # Warranty date filters (exact and range)
    warranty_start = forms.DateField(required=False, label=("Warranty Start"), widget=DatePicker())
    warranty_start__gte = forms.DateField(required=False, label=("Warranty Start: From"), widget=DatePicker())
    warranty_start__lte = forms.DateField(required=False, label=("Warranty Start: Till"), widget=DatePicker())
    warranty_end = forms.DateField(required=False, label=("Warranty End"), widget=DatePicker())
    warranty_end__gte = forms.DateField(required=False, label=("Warranty End: From"), widget=DatePicker())
    warranty_end__lte = forms.DateField(required=False, label=("Warranty End: Till"), widget=DatePicker())

    has_abra_assets = forms.ChoiceField(
        choices=[
            ("", "All"),
            ("true", "With ABRA assets"),
            ("false", "Without ABRA assets"),
        ],
        required=False,
        label=_("Has ABRA assets"),
        help_text=_("Filter by whether Asset object has assigned ABRA assets"),
    )


class AssetBulkEditForm(NetBoxModelBulkEditForm):
    name = forms.CharField(
        required=False,
        label="Name",
        widget=forms.TextInput(attrs={"placeholder": "Name"}),
    )
    type = DynamicModelChoiceField(queryset=AssetType.objects.all(), required=False)

    assignment_status = forms.ChoiceField(choices=add_blank_choice(AssignmentStatusChoices), required=False)

    lifecycle_status = forms.ChoiceField(choices=add_blank_choice(LifecycleStatusChoices), required=False)

    project = forms.CharField(required=False)

    vendor = forms.CharField(required=False)

    order_contract = DynamicModelChoiceField(queryset=Contract.objects.all(), required=False)

    warranty_start = forms.DateField(required=False, widget=DatePicker())

    warranty_end = forms.DateField(required=False, widget=DatePicker())

    comments = CommentField(required=False)

    model = Asset  # Add this line to explicitly define the model at the class level

    class Meta:
        model = Asset
        fields = [
            "name",
            "type",
            "assignment_status",
            "lifecycle_status",
            "project",
            "vendor",
            "order_contract",
            "warranty_start",
            "warranty_end",
            "comments",
            "tags",
        ]
