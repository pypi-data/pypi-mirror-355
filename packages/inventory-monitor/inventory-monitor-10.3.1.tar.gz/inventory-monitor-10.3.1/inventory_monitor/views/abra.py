from netbox.views import generic

from inventory_monitor.filtersets import ABRAFilterSet
from inventory_monitor.forms import ABRAFilterForm, ABRAForm
from inventory_monitor.models import ABRA
from inventory_monitor.tables import ABRATable


class ABRAView(generic.ObjectView):
    queryset = ABRA.objects.all()


class ABRAListView(generic.ObjectListView):
    queryset = ABRA.objects.all()
    table = ABRATable
    filterset = ABRAFilterSet
    filterset_form = ABRAFilterForm


class ABRAEditView(generic.ObjectEditView):
    queryset = ABRA.objects.all()
    form = ABRAForm


class ABRADeleteView(generic.ObjectDeleteView):
    queryset = ABRA.objects.all()


class ABRABulkImportView(generic.BulkImportView):
    queryset = ABRA.objects.all()
    model_form = ABRAForm


class ABRABulkEditView(generic.BulkEditView):
    queryset = ABRA.objects.all()
    filterset = ABRAFilterSet
    table = ABRATable


class ABRABulkDeleteView(generic.BulkDeleteView):
    queryset = ABRA.objects.all()
    table = ABRATable
