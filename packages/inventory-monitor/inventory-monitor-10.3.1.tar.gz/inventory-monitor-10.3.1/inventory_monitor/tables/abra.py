import django_tables2 as tables
from netbox.tables import NetBoxTable

from inventory_monitor.models import ABRA

ASSOCIATED_ASSETS = """
  {% if value.count > 3 %}
    <a href="{% url 'plugins:inventory_monitor:asset_list' %}?abra_assets={{ record.pk }}">{{ value.count }}</a>
  {% else %}
    {% for asset in value.all %}
      {% if asset.get_lifecycle_status_display != 'Active' %}
        <a href="{{ asset.get_absolute_url }}" class="badge text-bg-{{ asset.get_lifecycle_status_color }}" data-bs-toggle="tooltip" data-bs-placement="left" title="{{ asset.get_lifecycle_status_display }}">{{ asset }}</a>
      {% else %}
        <a href="{{ asset.get_absolute_url }}">{{ asset }}</a>
      {% endif %}
    {% endfor %}
  {% endif %}
"""


class ABRATable(NetBoxTable):
    """
    Table configuration for displaying ABRA objects in list views
    """

    abra_id = tables.Column(linkify=True)  # Add this field
    inventory_number = tables.Column(linkify=True)
    name = tables.Column()
    serial_number = tables.Column()
    person_name = tables.Column()
    location = tables.Column()
    assets = tables.TemplateColumn(template_code=ASSOCIATED_ASSETS, orderable=False, verbose_name="Assets")

    class Meta(NetBoxTable.Meta):
        model = ABRA
        fields = (
            "pk",
            "id",
            "abra_id",
            "inventory_number",
            "name",
            "serial_number",
            "person_id",
            "person_name",
            "location_code",
            "location",
            "department_code",
            "project_code",
            "user_name",
            "split_asset",
            "status",
            "assets",
            "actions",
        )
        default_columns = (
            "id",
            "abra_id",
            "inventory_number",
            "name",
            "serial_number",
            "person_name",
            "location",
            "status",
            "assets",
            "actions",
        )
