import django_tables2 as tables
from netbox.tables import NetBoxTable, columns

# Helper imports for custom columns and templates
from inventory_monitor.helpers import (
    TEMPLATE_SERVICES_CONTRACTS,
    TEMPLATE_SERVICES_END,
    NumberColumn,
)
from inventory_monitor.models import Asset

ASSOCIATED_ABRA_ASSETS = """
  {% if value.count > 3 %}
    <a href="{% url 'plugins:inventory_monitor:abra_list' %}?asset_id={{ record.pk }}">{{ value.count }}</a>
  {% else %}
    {% for abra in value.all %}
        <a href="{{ abra.get_absolute_url }}" class="badge text-bg-{% if abra.status == '1' %}green{% elif abra.status == '0' %}gray{% else %}blue{% endif %}" data-bs-toggle="tooltip" data-bs-placement="left" title="Status: {{ abra.status|default:'Unknown' }}">{{abra.inventory_number}}: {{abra.name}}</a>
    {% endfor %}
  {% endif %}
"""


class AssetTable(NetBoxTable):
    """
    Table configuration for displaying Asset objects in list views
    """

    #
    # Basic identification columns
    #
    description = tables.Column()
    serial = tables.Column(linkify=True)
    partnumber = tables.Column()
    abra_asset_numbers = tables.TemplateColumn(
        template_code="""
        {% if record.get_abra_asset_numbers_display %}
            {{ record.get_abra_asset_numbers_display }}
        {% else %}
            {{ ''|placeholder }}
        {% endif %}
        """,
        verbose_name="Asset Number(s)",
        orderable=False,
    )

    #
    # Type and classification columns
    #
    type = columns.TemplateColumn(
        template_code="""
        {% if record.type %}
            <a href="{{ record.type.get_absolute_url }}">
                {% if record.type.color %}
                    <span class="badge" style="background-color: #{{ record.type.color }}">
                        {{ record.type.name }}
                    </span>
                {% else %}
                    {{ record.type.name }}
                {% endif %}
            </a>
        {% endif %}
        """,
        verbose_name="Type",
        orderable=True,
    )

    #
    # Status columns
    #
    assignment_status = columns.ChoiceFieldColumn()
    lifecycle_status = columns.ChoiceFieldColumn()

    # Formatted column for warranty status using a template
    warranty_status = tables.TemplateColumn(
        template_code="""
            {% include 'inventory_monitor/inc/status_badge.html' with status_type='warranty' %}
        """,
        verbose_name="Warranty Status",
        orderable=False,
    )

    #
    # Assignment columns
    #
    assigned_object = tables.Column(verbose_name="Assigned Object", orderable=False, linkify=True)
    abra_assets = tables.TemplateColumn(
        template_code=ASSOCIATED_ABRA_ASSETS,
        orderable=False,
        verbose_name="ABRA Assets",
    )

    #
    # Related object columns
    #
    order_contract = tables.Column(linkify=True)

    #
    # Additional information columns
    #
    project = tables.Column()
    vendor = tables.Column()
    quantity = tables.Column()
    price = NumberColumn()  # Custom column for proper price formatting

    #
    # Service information columns
    #
    services_to = columns.TemplateColumn(template_code=TEMPLATE_SERVICES_END, verbose_name="Service End")
    services_contracts = tables.TemplateColumn(
        template_code=TEMPLATE_SERVICES_CONTRACTS, verbose_name="Service Contracts"
    )

    #
    # Warranty information columns
    #
    warranty_start = tables.Column()
    warranty_end = tables.Column()

    #
    # Metadata columns
    #
    tags = columns.TagColumn()
    comments = tables.Column()

    class Meta(NetBoxTable.Meta):
        model = Asset

        # Define all available fields that can be displayed in the table
        fields = (
            # Key identifiers
            "pk",
            "id",
            "partnumber",
            # Basic identification
            "serial",
            "abra_asset_numbers",
            "description",
            # Type and classification
            "type",
            # Status
            "assignment_status",
            "lifecycle_status",
            # Assignment
            "assigned_object",
            "abra_assets",
            # Additional information
            "project",
            "vendor",
            "quantity",
            "price",
            # Related objects
            "order_contract",
            # Warranty information
            "warranty_start",
            "warranty_end",
            "warranty_status",
            # Service information
            "services_count",
            "services_contracts",
            "services_to",
            # Metadata
            "comments",
            "tags",
            "actions",
        )

        # Define the default columns that are shown when the table first loads
        default_columns = (
            "id",
            "partnumber",
            "serial",
            "description",
            "type",
            "assigned_object",
            "assignment_status",
            "lifecycle_status",
            "abra_asset_numbers",
            "actions",
        )
