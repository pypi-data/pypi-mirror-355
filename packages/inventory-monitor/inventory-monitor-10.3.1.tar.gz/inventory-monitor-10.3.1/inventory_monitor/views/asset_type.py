from netbox.views import generic
from utilities.query import count_related
from utilities.views import GetRelatedModelsMixin

from inventory_monitor import filtersets, forms, models, tables


class AssetTypeView(GetRelatedModelsMixin, generic.ObjectView):
    queryset = models.AssetType.objects.all()

    def get_extra_context(self, request, instance):
        return {
            "related_models": self.get_related_models(request, instance),
        }


class AssetTypeListView(generic.ObjectListView):
    queryset = models.AssetType.objects.annotate(asset_count=count_related(models.Asset, "type"))
    table = tables.AssetTypeTable
    filterset = filtersets.AssetTypeFilterSet
    filterset_form = forms.AssetTypeFilterForm


class AssetTypeEditView(generic.ObjectEditView):
    queryset = models.AssetType.objects.all()
    form = forms.AssetTypeForm


class AssetTypeDeleteView(generic.ObjectDeleteView):
    queryset = models.AssetType.objects.all()
