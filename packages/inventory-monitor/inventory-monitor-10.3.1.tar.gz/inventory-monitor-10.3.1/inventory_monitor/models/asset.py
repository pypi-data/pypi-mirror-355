from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse
from netbox.models import ImageAttachmentsMixin, NetBoxModel
from utilities.choices import ChoiceSet
from utilities.querysets import RestrictedQuerySet

from inventory_monitor.models.mixins import DateStatusMixin
from inventory_monitor.models.probe import Probe

ASSIGNED_OBJECT_MODELS_QUERY = Q(
    app_label="dcim",
    model__in=(
        "site",
        "location",
        "rack",
        "device",
        "module",
    ),
)


class AssignmentStatusChoices(ChoiceSet):
    key = "inventory_monitor.asset.assignment_status"

    RESERVED = "reserved"
    DEPLOYED = "deployed"
    LOANED = "loaned"
    STOCKED = "stocked"

    CHOICES = [
        (RESERVED, "Reserved", "cyan"),
        (DEPLOYED, "Deployed", "green"),
        (LOANED, "Loaned", "blue"),
        (STOCKED, "Stocked", "gray"),
    ]


class LifecycleStatusChoices(ChoiceSet):
    key = "inventory_monitor.asset.lifecycle_status"

    NEW = "new"
    IN_STOCK = "in_stock"
    IN_USE = "in_use"
    IN_MAINTENANCE = "in_maintenance"
    RETIRED = "retired"
    DISPOSED = "disposed"

    CHOICES = [
        (NEW, "New", "green"),
        (IN_STOCK, "In Stock", "blue"),
        (IN_USE, "In Use", "cyan"),
        (IN_MAINTENANCE, "In Maintenance", "orange"),
        (RETIRED, "Retired", "red"),
        (DISPOSED, "Disposed", "gray"),
    ]


class Asset(NetBoxModel, DateStatusMixin, ImageAttachmentsMixin):
    objects = RestrictedQuerySet.as_manager()

    #
    # Basic identification fields
    #
    partnumber = models.CharField(max_length=64, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    serial = models.CharField(max_length=255, blank=False, null=False)
    #
    # Status fields
    #
    assignment_status = models.CharField(
        max_length=30,
        choices=AssignmentStatusChoices,
        default=AssignmentStatusChoices.STOCKED,
        blank=False,
        null=False,
    )
    lifecycle_status = models.CharField(
        max_length=30,
        choices=LifecycleStatusChoices,
        default=LifecycleStatusChoices.NEW,
        blank=False,
        null=False,
    )

    #
    # Assignment fields using GenericForeignKey
    #
    assigned_object_type = models.ForeignKey(
        to="contenttypes.ContentType",
        limit_choices_to=ASSIGNED_OBJECT_MODELS_QUERY,
        on_delete=models.PROTECT,
        related_name="+",
        blank=True,
        null=True,
    )
    assigned_object_id = models.PositiveBigIntegerField(blank=True, null=True)
    assigned_object = GenericForeignKey(ct_field="assigned_object_type", fk_field="assigned_object_id")

    #
    # Related objects
    #
    type = models.ForeignKey(
        to="inventory_monitor.AssetType",
        on_delete=models.PROTECT,
        related_name="assets",
        blank=True,
        null=True,
    )
    order_contract = models.ForeignKey(
        to="inventory_monitor.contract",
        on_delete=models.PROTECT,
        related_name="assets",
        blank=True,
        null=True,
    )

    #
    # Additional information
    #
    project = models.CharField(max_length=32, blank=True, null=True)
    vendor = models.CharField(max_length=32, blank=True, null=True)
    quantity = models.PositiveIntegerField(
        blank=False,
        null=False,
        default=1,
        validators=[MinValueValidator(0)],
    )
    price = models.DecimalField(
        max_digits=19,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        default=0,
    )

    #
    # Warranty information
    #
    warranty_start = models.DateField(
        blank=True,
        null=True,
    )
    warranty_end = models.DateField(
        blank=True,
        null=True,
    )

    #
    # Notes
    #
    comments = models.TextField(blank=True)

    class Meta:
        db_table = "inventory_monitor_asset"
        ordering = (
            "partnumber",
            "serial",
            "description",
            "project",
            "vendor",
            "quantity",
            "price",
            "order_contract",
            "warranty_start",
            "warranty_end",
        )
        indexes = [
            models.Index(fields=["description"], name="invmon_asset_desc_idx"),
            models.Index(fields=["serial"], name="invmon_asset_serial_idx"),
            models.Index(fields=["partnumber"], name="invmon_asset_partnumber_idx"),
            models.Index(fields=["assignment_status"], name="invmon_asset_assign_status_idx"),
            models.Index(fields=["lifecycle_status"], name="invmon_asset_lifecycle_idx"),
            models.Index(fields=["vendor"], name="invmon_asset_vendor_idx"),
            models.Index(fields=["project"], name="invmon_asset_project_idx"),
            models.Index(fields=["warranty_start"], name="invmon_asset_warr_start_idx"),
            models.Index(fields=["warranty_end"], name="invmon_asset_warr_end_idx"),
            models.Index(
                fields=["assigned_object_type", "assigned_object_id"],
                name="invmon_asset_assigned_obj_idx",
            ),
        ]

    def get_abra_asset_numbers_for_search(self):
        """Get ABRA inventory numbers as a single searchable string"""
        numbers = list(self.abra_assets.values_list("inventory_number", flat=True))
        return " ".join(numbers) if numbers else ""

    def get_related_probes(self):
        """
        Get all probe records related to this asset through various serial number matches:
        - serial (Current serial)
        - RMA serial numbers (from related RMAs)

        Returns:
        - QuerySet of Probe objects ordered by time descending
        """

        serials = {self.serial}
        rma_original_serials = set(self.rmas.values_list("original_serial", flat=True))
        rma_replacement_serials = set(self.rmas.values_list("replacement_serial", flat=True))

        # add rma_original_serials and rma_replacement_serials to serials
        serials.update(rma_original_serials)
        serials.update(rma_replacement_serials)
        # get rid of None values
        serials = [s for s in serials if s]

        return Probe.objects.filter(serial__in=serials).order_by("-time")

    def get_abra_asset_numbers(self):
        """Get all ABRA inventory numbers associated with this asset"""
        return self.abra_assets.values_list("inventory_number", flat=True)

    def get_abra_asset_numbers_display(self):
        """Get formatted display of ABRA asset numbers"""
        numbers = list(self.get_abra_asset_numbers())
        if not numbers:
            return None
        elif len(numbers) == 1:
            return numbers[0]
        else:
            return ", ".join(numbers)

    def __str__(self):
        if self.partnumber:
            return f"{self.partnumber} ({self.serial})"
        return f"{self.serial}"

    def get_absolute_url(self):
        return reverse("plugins:inventory_monitor:asset", args=[self.pk])

    def clean(self):
        super().clean()

    def get_assignment_status_color(self):
        return AssignmentStatusChoices.colors.get(self.assignment_status, "gray")

    def get_lifecycle_status_color(self):
        return LifecycleStatusChoices.colors.get(self.lifecycle_status, "gray")

    def get_warranty_status(self):
        """Returns the warranty status and color for progress bar"""
        return self.get_date_status("warranty_start", "warranty_end", "Warranty")
