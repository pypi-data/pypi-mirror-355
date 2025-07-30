from netbox.views import generic

from inventory_monitor import filtersets, forms, models, tables


class RMAView(generic.ObjectView):
    queryset = models.RMA.objects.all()


class RMAListView(generic.ObjectListView):
    queryset = models.RMA.objects.select_related("asset")
    table = tables.RMATable
    filterset = filtersets.RMAFilterSet
    filterset_form = forms.RMAFilterForm
    # actions = ['add', 'import', 'export', 'bulk_edit', 'bulk_delete']


class RMAEditView(generic.ObjectEditView):
    queryset = models.RMA.objects.all()
    form = forms.RMAForm


class RMADeleteView(generic.ObjectDeleteView):
    queryset = models.RMA.objects.all()
