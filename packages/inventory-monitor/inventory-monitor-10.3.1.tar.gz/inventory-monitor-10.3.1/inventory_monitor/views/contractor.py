from core.models import ObjectType
from django.db.models import Count, OuterRef, Subquery
from netbox.views import generic

from inventory_monitor import filtersets, forms, models, tables
from inventory_monitor.helpers import get_object_type_or_none

# Attempt to import NetBoxAttachment and set a flag based on its availability
attachments_model_exists = False
try:
    from netbox_attachments.models import NetBoxAttachment

    attachments_model_exists = True
except (ModuleNotFoundError, RuntimeError):
    pass


def annotate_contracts_with_attachments(contracts, instance):
    try:
        contract_object_type = get_object_type_or_none(app_label="inventory_monitor", model="contract")
        subquery_attachments_count = (
            NetBoxAttachment.objects.filter(object_id=OuterRef("id"), object_type=contract_object_type)
            .values("object_id")
            .annotate(attachments_count=Count("*"))
        )
        return contracts.annotate(attachments_count=Subquery(subquery_attachments_count.values("attachments_count")))
    except (ObjectType.DoesNotExist, ValueError):
        # Return contracts without attachment count if there's an error
        return contracts


class ContractorView(generic.ObjectView):
    queryset = models.Contractor.objects.all()


class ContractorListView(generic.ObjectListView):
    queryset = models.Contractor.objects.prefetch_related("tags").annotate(contracts_count=Count("contracts"))
    filterset = filtersets.ContractorFilterSet
    filterset_form = forms.ContractorFilterForm
    table = tables.ContractorTable


class ContractorEditView(generic.ObjectEditView):
    queryset = models.Contractor.objects.all()
    form = forms.ContractorForm


class ContractorDeleteView(generic.ObjectDeleteView):
    queryset = models.Contractor.objects.all()
