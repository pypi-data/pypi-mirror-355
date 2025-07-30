from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.aggregates.general import ArrayAgg
from django.db.models import Count
from netbox.views import generic

from inventory_monitor import filtersets, forms, models, tables


class AssetView(generic.ObjectView):
    queryset = models.Asset.objects.all()


class AssetListView(generic.ObjectListView):
    queryset = (
        models.Asset.objects.all()
        .prefetch_related("services")
        .prefetch_related("tags")
        .prefetch_related("abra_assets")
        .annotate(services_count=Count("services"))
        .annotate(services_to=ArrayAgg("services__service_end"))
        .annotate(services_contracts=ArrayAgg("services__contract__name"))
    )
    filterset = filtersets.AssetFilterSet
    filterset_form = forms.AssetFilterForm
    table = tables.AssetTable
    actions = {
        "add": {},
        "import": {},
        "export": {},
        "bulk_edit": {},
        "bulk_delete": {},
    }


class AssetEditView(generic.ObjectEditView):
    queryset = models.Asset.objects.all()
    form = forms.AssetForm

    def alter_object(self, instance, request, url_args, url_kwargs):
        if not instance.pk:
            assigned_object_type = request.GET.get("assigned_object_type")
            assigned_object_id = request.GET.get("assigned_object_id")

            if assigned_object_type and assigned_object_id:
                instance.assigned_object_type = ContentType.objects.get(pk=assigned_object_type)
                instance.assigned_object_id = assigned_object_id

        return instance


class AssetDeleteView(generic.ObjectDeleteView):
    queryset = models.Asset.objects.all()


class AssetBulkEditView(generic.BulkEditView):
    queryset = models.Asset.objects.all()
    filterset = filtersets.AssetFilterSet
    table = tables.AssetTable
    form = forms.AssetBulkEditForm


class AssetBulkDeleteView(generic.BulkDeleteView):
    queryset = models.Asset.objects.all()
    filterset = filtersets.AssetFilterSet
    table = tables.AssetTable
