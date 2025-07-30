from django.db import models
from django.urls import reverse
from django.utils import timezone
from netbox.models.features import (
    CustomFieldsMixin,
    CustomLinksMixin,
    CustomValidationMixin,
    EventRulesMixin,
    ExportTemplatesMixin,
    JournalingMixin,
    TagsMixin,
)
from utilities.querysets import RestrictedQuerySet


class Probe(
    CustomFieldsMixin,
    CustomLinksMixin,
    CustomValidationMixin,
    ExportTemplatesMixin,
    JournalingMixin,
    TagsMixin,
    EventRulesMixin,
    models.Model,
):
    objects = RestrictedQuerySet.as_manager()
    time = models.DateTimeField()
    creation_time = models.DateTimeField(default=timezone.now, blank=True, null=True)
    device_descriptor = models.CharField(max_length=100, blank=True, null=True)
    site_descriptor = models.CharField(max_length=100, blank=True, null=True)
    location_descriptor = models.CharField(max_length=100, blank=True, null=True)
    part = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255)
    serial = models.CharField(max_length=255)
    device = models.ForeignKey(
        to="dcim.Device",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    site = models.ForeignKey(
        to="dcim.Site",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    location = models.ForeignKey(
        to="dcim.Location",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    description = models.TextField(blank=True)
    comments = models.TextField(blank=True)
    discovered_data = models.JSONField(default=dict, blank=True)
    category = models.CharField(blank=True, null=True, max_length=255)

    class Meta:
        indexes = [
            models.Index(fields=["serial"], name="invmon_probe_serial_idx"),
            models.Index(fields=["time"], name="invmon_probe_time_idx"),
            models.Index(fields=["serial", "time"], name="invmon_probe_serial_time_idx"),
        ]
        ordering = (
            "name",
            "serial",
            "time",
            "part",
            "description",
            "device_descriptor",
            "device",
            "site_descriptor",
            "site",
            "location_descriptor",
            "location",
            "category",
            "discovered_data",
        )

    def __str__(self):
        return f"{self.serial} - {self.name}"

    def get_absolute_url(self):
        return reverse("plugins:inventory_monitor:probe", args=[self.pk])
