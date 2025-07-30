"""
Template Extensions and Views for Inventory Monitor Plugin.

This module provides NetBox UI customizations including:
- Template extensions for displaying inventory data
- Custom views for assets and probes
- Dynamic view registration for different model types
- Hierarchical asset display across NetBox object relationships
"""

from typing import Any, Dict, List, Set, Type

from dcim.models import Device, Location, Module, Rack, Site
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, QuerySet
from django.http import HttpRequest
from netbox.plugins import PluginTemplateExtension
from netbox.views import generic
from utilities.views import ViewTab, register_model_view

from inventory_monitor.filtersets import AssetFilterSet, ProbeFilterSet
from inventory_monitor.models import Asset, Contract, Contractor, Probe
from inventory_monitor.tables import AssetTable, ProbeTable

# Load plugin configuration settings
plugin_settings = settings.PLUGINS_CONFIG.get("inventory_monitor", {})


class TenantContractorExtension(PluginTemplateExtension):
    """Display contractor information on tenant detail page."""

    models = ["tenancy.tenant"]

    def left_page(self) -> str:
        """Show contractor details in the left sidebar."""
        # Find contractor associated with this tenant
        contractor = Contractor.objects.filter(tenant_id=self.context["object"].pk).first()

        # Count contracts if contractor exists
        contracts_count = contractor.contracts.count() if contractor else 0

        return self.render(
            "inventory_monitor/inc/tenant_contractor_extension.html",
            extra_context={
                "contractor": contractor,
                "contracts_count": contracts_count,
            },
        )


class AbraAssetsExtension(PluginTemplateExtension):
    """Display assets information on abra detail page."""

    models = ["inventory_monitor.abra"]

    def full_width_page(self) -> str:
        """Show asset details in the full_width_page."""
        return self.render(
            "inventory_monitor/inc/abra_asset_extension.html",
        )


class AbraRMAsExtension(PluginTemplateExtension):
    """Display assets information on abra detail page."""

    models = ["inventory_monitor.abra"]

    def full_width_page(self) -> str:
        """Show asset details in the full_width_page."""
        return self.render(
            "inventory_monitor/inc/abra_rma_extension.html",
        )


class ProbeAssetExtension(PluginTemplateExtension):
    """Display assets with matching serial number on probe detail page."""

    models = ["inventory_monitor.probe"]

    def right_page(self) -> str:
        """Display matching assets in the full width section of the page."""
        probe = self.context["object"]

        # Find assets that match any of these criteria:
        # 1. Current asset serial matches probe serial
        # 2. Asset has an RMA where original_serial matches probe serial
        # 3. Asset has an RMA where replacement_serial matches probe serial
        matching_assets = Asset.objects.filter(
            Q(serial=probe.serial) | Q(rmas__original_serial=probe.serial) | Q(rmas__replacement_serial=probe.serial)
        ).distinct()

        # Create asset table for display
        asset_table = AssetTable(matching_assets)

        return self.render(
            "inventory_monitor/inc/probe_asset_extension.html",
            extra_context={
                "assets": matching_assets,
                "asset_table": asset_table,
                "assets_count": matching_assets.count(),
            },
        )


class AssetDuplicates(PluginTemplateExtension):
    """Show potential duplicate assets with the same serial number or RMA relationships."""

    models = ["inventory_monitor.asset"]

    def full_width_page(self) -> str:
        """Display duplicate assets in the full width section of the page."""
        current_asset = self.context["object"]

        # Instead of combining querysets, let's get all potential candidates first
        # Then filter them in Python to avoid SQL-level combination issues
        potential_duplicates_ids = set()

        # Track different duplicate types separately
        direct_duplicates_ids = set()
        rma_duplicates_ids = set()
        reverse_rma_duplicates_ids = set()

        # Find direct duplicates (same serial)
        if current_asset.serial:
            direct_dups = (
                Asset.objects.filter(serial=current_asset.serial)
                .exclude(id=current_asset.id)
                .values_list("id", flat=True)
            )

            direct_duplicates_ids.update(direct_dups)
            potential_duplicates_ids.update(direct_dups)

        # Find assets that have this serial in their RMAs
        if current_asset.serial:
            rma_dups = (
                Asset.objects.filter(
                    Q(rmas__original_serial=current_asset.serial) | Q(rmas__replacement_serial=current_asset.serial)
                )
                .exclude(id=current_asset.id)
                .values_list("id", flat=True)
                .distinct()
            )

            rma_duplicates_ids.update(rma_dups)
            potential_duplicates_ids.update(rma_dups)

        # Find assets where this asset's serial appears in their RMA records
        if current_asset.serial and hasattr(current_asset, "rmas") and current_asset.rmas.exists():
            # Get the RMA serials
            original_serials = [s for s in list(current_asset.rmas.values_list("original_serial", flat=True)) if s]
            replacement_serials = [
                s for s in list(current_asset.rmas.values_list("replacement_serial", flat=True)) if s
            ]

            if original_serials or replacement_serials:
                # Create a list of all serials to search for
                all_serials = original_serials + replacement_serials

                # Get assets with matching serials in a single query
                reverse_rma_dups = (
                    Asset.objects.filter(serial__in=all_serials)
                    .exclude(id=current_asset.id)
                    .values_list("id", flat=True)
                    .distinct()
                )

                reverse_rma_duplicates_ids.update(reverse_rma_dups)
                potential_duplicates_ids.update(reverse_rma_dups)

        # Now that we have all IDs, fetch the full asset objects in a single query
        all_duplicates = Asset.objects.filter(id__in=list(potential_duplicates_ids))

        # Calculate counts
        direct_duplicates_count = len(direct_duplicates_ids)
        rma_duplicates_count = len(rma_duplicates_ids)
        reverse_rma_duplicates_count = len(reverse_rma_duplicates_ids)

        return self.render(
            "inventory_monitor/inc/asset_duplicates_extension.html",
            extra_context={
                "current_asset": current_asset,
                "duplicates": all_duplicates,
                "duplicates_count": len(potential_duplicates_ids),
                "direct_duplicates_count": direct_duplicates_count,
                "rma_duplicates_count": rma_duplicates_count,
                "reverse_rma_duplicates_count": reverse_rma_duplicates_count,
            },
        )


@register_model_view(Asset, name="probes", path="probes")
class AssetProbesView(generic.ObjectChildrenView):
    """Provides a 'Probes' tab on asset detail pages showing related probe records."""

    queryset = Asset.objects.all()
    child_model = Probe
    table = ProbeTable
    filterset = ProbeFilterSet
    template_name = "generic/object_children.html"
    hide_if_empty = False
    tab = ViewTab(
        label="Probes",
        badge=lambda obj: obj.get_related_probes().count(),
        permission="inventory_monitor.view_probe",
    )

    def get_children(self, request: HttpRequest, parent: Asset) -> QuerySet[Probe]:
        """Retrieve all probes related to this asset."""
        return parent.get_related_probes()


@register_model_view(Contract, name="assets", path="assets")
class ContractAssetsView(generic.ObjectChildrenView):
    """View to display assets ordered through this contract."""

    queryset = Contract.objects.all()
    child_model = Asset
    filterset = AssetFilterSet
    table = AssetTable
    template_name = "generic/object_children.html"
    hide_if_empty = False
    tab = ViewTab(
        label="Assets",
        badge=lambda obj: obj.assets.count(),
        permission="inventory_monitor.view_asset",
    )

    def get_children(self, request: HttpRequest, parent: Contract) -> QuerySet[Asset]:
        """Get assets where this contract is the order_contract."""
        return parent.assets.all()


class AssignedAssetsView(generic.ObjectChildrenView):
    """
    Base class for views that display assets assigned to any object type.

    Supports hierarchical asset display showing assets assigned to an object
    and all its child objects (e.g., Site -> Location -> Device -> Module).
    """

    child_model = Asset
    table = AssetTable
    template_name = "inventory_monitor/asset_children.html"
    filterset = AssetFilterSet
    hide_if_empty = False

    # Cache for content types to avoid repeated database queries
    _content_types: Dict[str, ContentType] = {}

    @staticmethod
    def get_hierarchical_asset_ids(parent: Any) -> Set[int]:
        """
        Get all asset IDs assigned to this object and its child objects hierarchically.

        Args:
            parent: The parent object (Site, Location, Rack, Device, or Module)

        Returns:
            Set of asset IDs including direct and hierarchical assignments
        """
        content_type = ContentType.objects.get_for_model(parent)

        # Start with assets directly assigned to this object
        asset_ids = set(
            Asset.objects.filter(assigned_object_type=content_type, assigned_object_id=parent.pk).values_list(
                "id", flat=True
            )
        )

        # Define hierarchy mapping for cleaner logic
        hierarchy_handlers = {
            Site: AssignedAssetsView._handle_site_hierarchy,
            Location: AssignedAssetsView._handle_location_hierarchy,
            Rack: AssignedAssetsView._handle_rack_hierarchy,
            Device: AssignedAssetsView._handle_device_hierarchy,
            # Module has no children, only direct assets
        }

        handler = hierarchy_handlers.get(type(parent))
        if handler:
            handler(parent, asset_ids)

        return asset_ids

    @staticmethod
    def _get_content_types() -> Dict[str, ContentType]:
        """
        Cache content types to avoid repeated queries.

        Returns:
            Dictionary mapping model names to their ContentType objects
        """
        if not AssignedAssetsView._content_types:
            AssignedAssetsView._content_types = {
                "location": ContentType.objects.get_for_model(Location),
                "device": ContentType.objects.get_for_model(Device),
                "module": ContentType.objects.get_for_model(Module),
            }
        return AssignedAssetsView._content_types

    @staticmethod
    def _add_assets_for_objects(asset_ids: Set[int], content_type: ContentType, object_ids: List[int]) -> None:
        """
        Helper to add asset IDs for given objects.

        Args:
            asset_ids: Set to update with new asset IDs
            content_type: ContentType of the objects
            object_ids: List of object IDs to find assets for
        """
        if object_ids:
            new_asset_ids = Asset.objects.filter(
                assigned_object_type=content_type, assigned_object_id__in=object_ids
            ).values_list("id", flat=True)
            asset_ids.update(new_asset_ids)

    @staticmethod
    def _handle_site_hierarchy(site: Site, asset_ids: Set[int]) -> None:
        """
        Handle asset hierarchy for Site objects.

        Includes assets from: Site -> Locations -> Devices -> Modules

        Args:
            site: The Site object
            asset_ids: Set to update with found asset IDs
        """
        cts = AssignedAssetsView._get_content_types()

        # Get all locations in this site
        location_ids = list(Location.objects.filter(site=site).values_list("id", flat=True))
        AssignedAssetsView._add_assets_for_objects(asset_ids, cts["location"], location_ids)

        # Get all devices in this site
        device_ids = list(Device.objects.filter(site=site).values_list("id", flat=True))
        AssignedAssetsView._add_assets_for_objects(asset_ids, cts["device"], device_ids)

        # Get all modules in devices of this site
        if device_ids:
            module_ids = list(Module.objects.filter(device_id__in=device_ids).values_list("id", flat=True))
            AssignedAssetsView._add_assets_for_objects(asset_ids, cts["module"], module_ids)

    @staticmethod
    def _handle_location_hierarchy(location: Location, asset_ids: Set[int]) -> None:
        """
        Handle asset hierarchy for Location objects.

        Includes assets from: Location -> Descendant Locations -> Devices -> Modules

        Args:
            location: The Location object
            asset_ids: Set to update with found asset IDs
        """
        cts = AssignedAssetsView._get_content_types()

        # Include current location and all descendant locations
        descendant_ids = list(location.get_descendants().values_list("id", flat=True))
        location_scope_ids = [location.id] + descendant_ids

        # Add assets from descendant locations
        AssignedAssetsView._add_assets_for_objects(asset_ids, cts["location"], descendant_ids)

        # Get devices in this location and all descendant locations
        device_ids = list(Device.objects.filter(location_id__in=location_scope_ids).values_list("id", flat=True))
        AssignedAssetsView._add_assets_for_objects(asset_ids, cts["device"], device_ids)

        # Get modules in those devices
        if device_ids:
            module_ids = list(Module.objects.filter(device_id__in=device_ids).values_list("id", flat=True))
            AssignedAssetsView._add_assets_for_objects(asset_ids, cts["module"], module_ids)

    @staticmethod
    def _handle_rack_hierarchy(rack: Rack, asset_ids: Set[int]) -> None:
        """
        Handle asset hierarchy for Rack objects.

        Includes assets from: Rack -> Devices -> Modules

        Args:
            rack: The Rack object
            asset_ids: Set to update with found asset IDs
        """
        cts = AssignedAssetsView._get_content_types()

        # Get devices in this rack
        device_ids = list(Device.objects.filter(rack=rack).values_list("id", flat=True))
        AssignedAssetsView._add_assets_for_objects(asset_ids, cts["device"], device_ids)

        # Get modules in those devices
        if device_ids:
            module_ids = list(Module.objects.filter(device_id__in=device_ids).values_list("id", flat=True))
            AssignedAssetsView._add_assets_for_objects(asset_ids, cts["module"], module_ids)

    @staticmethod
    def _handle_device_hierarchy(device: Device, asset_ids: Set[int]) -> None:
        """
        Handle asset hierarchy for Device objects.

        Includes assets from: Device -> Modules

        Args:
            device: The Device object
            asset_ids: Set to update with found asset IDs
        """
        cts = AssignedAssetsView._get_content_types()

        # Get modules in this device
        module_ids = list(Module.objects.filter(device=device).values_list("id", flat=True))
        AssignedAssetsView._add_assets_for_objects(asset_ids, cts["module"], module_ids)

    @staticmethod
    def count_hierarchical_assets(parent: Any) -> int:
        """
        Count all assets assigned to this object and its child objects hierarchically.

        Args:
            parent: The parent object to count assets for

        Returns:
            Total count of assets including hierarchical relationships
        """
        return len(AssignedAssetsView.get_hierarchical_asset_ids(parent))

    def get_children(self, request: HttpRequest, parent: Any) -> QuerySet[Asset]:
        """
        Get assets assigned to this object and its child objects hierarchically.

        Args:
            request: The HTTP request object
            parent: The parent object to get assets for

        Returns:
            QuerySet of assets including hierarchical relationships
        """
        asset_ids = self.get_hierarchical_asset_ids(parent)
        return Asset.objects.filter(id__in=asset_ids)


def asset_view_for_model(model: Type) -> Type:
    """
    Decorator to create and register an asset view for a model.

    Args:
        model: The Django model to create an asset view for

    Returns:
        The created view class
    """
    class_name = f"{model.__name__}AssetsView"

    view_class = type(
        class_name,
        (AssignedAssetsView,),
        {
            "queryset": model.objects.all(),
            "tab": ViewTab(
                label="Assets",
                badge=lambda obj: AssignedAssetsView.count_hierarchical_assets(obj),
                permission="inventory_monitor.view_asset",
            ),
        },
    )

    # Register the view
    return register_model_view(model, name="assets", path="assets")(view_class)


# Supported models for asset views
SUPPORTED_MODELS: List[Type] = [Site, Location, Rack, Device, Module]

# Create and register asset views for all supported models
asset_views = [asset_view_for_model(model) for model in SUPPORTED_MODELS]

# Template extensions to be registered by the plugin
template_extensions = [
    ProbeAssetExtension,
    TenantContractorExtension,
    AssetDuplicates,
    AbraAssetsExtension,
    AbraRMAsExtension,
]
