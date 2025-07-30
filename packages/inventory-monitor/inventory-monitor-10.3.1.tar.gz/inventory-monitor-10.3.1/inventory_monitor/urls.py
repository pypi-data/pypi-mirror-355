from django.urls import include, path
from netbox.views.generic import ObjectChangeLogView
from utilities.urls import get_model_urls

from inventory_monitor import models, views

app_name = "inventory_monitor"  # Add this line to define the app namespace

urlpatterns = (
    ## Probes
    path("probes/", views.ProbeListView.as_view(), name="probe_list"),
    path("probes/add/", views.ProbeEditView.as_view(), name="probe_add"),
    path("probes/<int:pk>/", views.ProbeView.as_view(), name="probe"),
    path("probes/<int:pk>/edit/", views.ProbeEditView.as_view(), name="probe_edit"),
    path("probes/<int:pk>/delete/", views.ProbeDeleteView.as_view(), name="probe_delete"),
    path(
        "probes/delete/",
        views.ProbeBulkDeleteView.as_view(),
        name="probe_bulk_delete",
    ),
    # INFO: Changelog needs to be add manually, cause Probe model is not derived from NetBoxModel
    path(
        "probes/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="probe_changelog",
        kwargs={"model": models.Probe},
    ),
    # Adds url's like changelog, journal, attachments (from plugin) and etc.
    path(
        "probes/<int:pk>/",
        include(get_model_urls("inventory_monitor", "probe")),
    ),
    path(
        "probes/",
        include(get_model_urls("inventory_monitor", "probe", detail=False)),
    ),
    ## Probe Diff
    path("probe_diff/", views.ProbeDiffView.as_view(), name="probediff"),
    ## Contractors
    path("contractors/", views.ContractorListView.as_view(), name="contractor_list"),
    path("contractors/add/", views.ContractorEditView.as_view(), name="contractor_add"),
    path("contractors/<int:pk>/", views.ContractorView.as_view(), name="contractor"),
    path(
        "contractors/<int:pk>/edit/",
        views.ContractorEditView.as_view(),
        name="contractor_edit",
    ),
    path(
        "contractors/<int:pk>/delete/",
        views.ContractorDeleteView.as_view(),
        name="contractor_delete",
    ),
    # Adds url's like changelog, journal, attachments (from plugin) and etc.
    path(
        "contractors/<int:pk>/",
        include(get_model_urls("inventory_monitor", "contractor")),
    ),
    path(
        "contractors/",
        include(get_model_urls("inventory_monitor", "contractor", detail=False)),
    ),
    ## Contracts
    path("contracts/", views.ContractListView.as_view(), name="contract_list"),
    path("contracts/add/", views.ContractEditView.as_view(), name="contract_add"),
    path("contracts/<int:pk>/", views.ContractView.as_view(), name="contract"),
    path(
        "contracts/<int:pk>/edit/",
        views.ContractEditView.as_view(),
        name="contract_edit",
    ),
    path(
        "contracts/<int:pk>/delete/",
        views.ContractDeleteView.as_view(),
        name="contract_delete",
    ),
    # Adds url's like changelog, journal, attachments (from plugin) and etc.
    path(
        "contracts/<int:pk>/",
        include(get_model_urls("inventory_monitor", "contract")),
    ),
    path(
        "contracts/",
        include(get_model_urls("inventory_monitor", "contract", detail=False)),
    ),
    ## Invoice
    path("invoices/", views.InvoiceListView.as_view(), name="invoice_list"),
    path("invoices/add/", views.InvoiceEditView.as_view(), name="invoice_add"),
    path("invoices/<int:pk>/", views.InvoiceView.as_view(), name="invoice"),
    path("invoices/<int:pk>/edit/", views.InvoiceEditView.as_view(), name="invoice_edit"),
    path(
        "invoices/<int:pk>/delete/",
        views.InvoiceDeleteView.as_view(),
        name="invoice_delete",
    ),
    # Adds url's like changelog, journal, attachments (from plugin) and etc.
    path(
        "invoices/<int:pk>/",
        include(get_model_urls("inventory_monitor", "invoice")),
    ),
    path(
        "invoices/",
        include(get_model_urls("inventory_monitor", "invoice", detail=False)),
    ),
    ## Asset
    path("assets/", views.AssetListView.as_view(), name="asset_list"),
    path("assets/add/", views.AssetEditView.as_view(), name="asset_add"),
    path("assets/edit/", views.AssetBulkEditView.as_view(), name="asset_bulk_edit"),
    path("assets/delete/", views.AssetBulkDeleteView.as_view(), name="asset_bulk_delete"),
    path("assets/<int:pk>/", views.AssetView.as_view(), name="asset"),
    path(
        "assets/<int:pk>/edit/",
        views.AssetEditView.as_view(),
        name="asset_edit",
    ),
    path(
        "assets/<int:pk>/delete/",
        views.AssetDeleteView.as_view(),
        name="asset_delete",
    ),
    # Adds url's like changelog, journal, attachments (from plugin) and etc.
    path(
        "assets/<int:pk>/",
        include(get_model_urls("inventory_monitor", "asset")),
    ),
    path(
        "assets/",
        include(get_model_urls("inventory_monitor", "asset", detail=False)),
    ),
    ## AssetType
    path("asset-types/", views.AssetTypeListView.as_view(), name="assettype_list"),
    path("asset-types/add/", views.AssetTypeEditView.as_view(), name="assettype_add"),
    path("asset-types/<int:pk>/", views.AssetTypeView.as_view(), name="assettype"),
    path(
        "asset-types/<int:pk>/edit/",
        views.AssetTypeEditView.as_view(),
        name="assettype_edit",
    ),
    path(
        "asset-types/<int:pk>/delete/",
        views.AssetTypeDeleteView.as_view(),
        name="assettype_delete",
    ),
    # Adds url's like changelog, journal, attachments (from plugin) and etc.
    path(
        "asset-types/<int:pk>/",
        include(get_model_urls("inventory_monitor", "assettype")),
    ),
    path(
        "asset-types/",
        include(get_model_urls("inventory_monitor", "assettype", detail=False)),
    ),
    ## ABRA
    path("abra/", views.ABRAListView.as_view(), name="abra_list"),
    path("abra/add/", views.ABRAEditView.as_view(), name="abra_add"),
    path("abra/<int:pk>/", views.ABRAView.as_view(), name="abra"),
    path("abra/<int:pk>/edit/", views.ABRAEditView.as_view(), name="abra_edit"),
    path("abra/<int:pk>/delete/", views.ABRADeleteView.as_view(), name="abra_delete"),
    path("abra/", include(get_model_urls("inventory_monitor", "abra"))),
    path(
        "abra/<int:pk>/",
        include(get_model_urls("inventory_monitor", "abra", detail=True)),
    ),
    ## AssetService
    path(
        "asset-services/",
        views.AssetServiceListView.as_view(),
        name="assetservice_list",
    ),
    path(
        "asset-services/add/",
        views.AssetServiceEditView.as_view(),
        name="assetservice_add",
    ),
    path(
        "asset-services/<int:pk>/",
        views.AssetServiceView.as_view(),
        name="assetservice",
    ),
    path(
        "asset-services/<int:pk>/edit/",
        views.AssetServiceEditView.as_view(),
        name="assetservice_edit",
    ),
    path(
        "asset-services/<int:pk>/delete/",
        views.AssetServiceDeleteView.as_view(),
        name="assetservice_delete",
    ),
    # Adds url's like changelog, journal, attachments (from plugin) and etc.
    path(
        "asset-services/<int:pk>/",
        include(get_model_urls("inventory_monitor", "assetservice")),
    ),
    path(
        "asset-services/",
        include(get_model_urls("inventory_monitor", "assetservice", detail=False)),
    ),
    ## RMA
    path("rmas/", views.RMAListView.as_view(), name="rma_list"),
    path("rmas/add/", views.RMAEditView.as_view(), name="rma_add"),
    path("rmas/<int:pk>/", views.RMAView.as_view(), name="rma"),
    path("rmas/<int:pk>/edit/", views.RMAEditView.as_view(), name="rma_edit"),
    path("rmas/<int:pk>/delete/", views.RMADeleteView.as_view(), name="rma_delete"),
    path("rmas/", include(get_model_urls("inventory_monitor", "rma"))),
    path(
        "rmas/<int:pk>/",
        include(get_model_urls("inventory_monitor", "rma", detail=True)),
    ),
)
