from netbox.views import generic

from inventory_monitor import filtersets, forms, models, tables


class AssetServiceView(generic.ObjectView):
    queryset = models.AssetService.objects.all()


class AssetServiceListView(generic.ObjectListView):
    queryset = models.AssetService.objects.all()
    filterset = filtersets.AssetServiceFilterSet
    filterset_form = forms.AssetServiceFilterForm
    table = tables.AssetServiceTable


class AssetServiceEditView(generic.ObjectEditView):
    queryset = models.AssetService.objects.all()
    form = forms.AssetServiceForm


class AssetServiceDeleteView(generic.ObjectDeleteView):
    queryset = models.AssetService.objects.all()
