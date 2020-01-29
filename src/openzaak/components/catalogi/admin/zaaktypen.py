from django.apps import apps
from django.contrib import admin
from django.db.models import Field
from django.http import HttpRequest
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from openzaak.selectielijst.admin_fields import get_procestype_field
from openzaak.utils.admin import (
    DynamicArrayMixin,
    EditInlineAdminMixin,
    ListObjectActionsAdminMixin,
    UUIDAdminMixin,
    link_to_related_objects,
)

from ..models import (
    Eigenschap,
    ResultaatType,
    RolType,
    StatusType,
    ZaakType,
    ZaakTypenRelatie,
)
from .eigenschap import EigenschapAdmin
from .forms import ZaakTypeForm
from .helpers import AdminForm
from .mixins import (
    CatalogusContextAdminMixin,
    ExportMixin,
    NewVersionMixin,
    PublishAdminMixin,
    ReadOnlyPublishedMixin,
    ReadOnlyPublishedZaaktypeMixin,
)
from .resultaattype import ResultaatTypeAdmin
from .roltype import RolTypeAdmin
from .statustype import StatusTypeAdmin


@admin.register(ZaakTypenRelatie)
class ZaakTypenRelatieAdmin(ReadOnlyPublishedZaaktypeMixin, admin.ModelAdmin):
    model = ZaakTypenRelatie

    # List
    list_display = ("gerelateerd_zaaktype", "zaaktype")
    list_filter = ("zaaktype", "aard_relatie")
    ordering = ("zaaktype", "gerelateerd_zaaktype")
    search_fields = ("gerelateerd_zaaktype", "toelichting", "zaaktype__uuid")

    # Detail
    fieldsets = (
        (
            _("Algemeen"),
            {"fields": ("gerelateerd_zaaktype", "aard_relatie", "toelichting")},
        ),
        (_("Relaties"), {"fields": ("zaaktype",)},),
    )
    raw_id_fields = ("zaaktype",)


class StatusTypeInline(EditInlineAdminMixin, admin.TabularInline):
    model = StatusType
    fields = StatusTypeAdmin.list_display
    fk_name = "zaaktype"


class RolTypeInline(EditInlineAdminMixin, admin.TabularInline):
    model = RolType
    fields = RolTypeAdmin.list_display
    fk_name = "zaaktype"


class EigenschapInline(EditInlineAdminMixin, admin.TabularInline):
    model = Eigenschap
    fields = EigenschapAdmin.list_display
    fk_name = "zaaktype"


class ResultaatTypeInline(EditInlineAdminMixin, admin.TabularInline):
    model = ResultaatType
    fields = ResultaatTypeAdmin.list_display
    fk_name = "zaaktype"


class ZaakTypenRelatieInline(EditInlineAdminMixin, admin.TabularInline):
    model = ZaakTypenRelatie
    fk_name = "zaaktype"
    fields = ZaakTypenRelatieAdmin.list_display


@admin.register(ZaakType)
class ZaakTypeAdmin(
    ReadOnlyPublishedMixin,
    NewVersionMixin,
    ListObjectActionsAdminMixin,
    UUIDAdminMixin,
    PublishAdminMixin,
    ExportMixin,
    DynamicArrayMixin,
    CatalogusContextAdminMixin,
    admin.ModelAdmin,
):
    model = ZaakType
    form = ZaakTypeForm

    # List
    list_display = (
        "zaaktype_omschrijving",
        "identificatie",
        "versiedatum",
        "is_published",
    )
    list_filter = (
        "catalogus",
        "publicatie_indicatie",
        "verlenging_mogelijk",
        "opschorting_en_aanhouding_mogelijk",
        "indicatie_intern_of_extern",
        "vertrouwelijkheidaanduiding",
    )
    ordering = ("catalogus", "identificatie")
    search_fields = (
        "uuid",
        "identificatie",
        "zaaktype_omschrijving",
        "zaaktype_omschrijving_generiek",
        "doel",
        "aanleiding",
        "onderwerp",
        "toelichting",
    )
    date_hierarchy = "versiedatum"

    # Details
    fieldsets = (
        (
            _("Algemeen"),
            {
                "fields": (
                    "identificatie",
                    "uuid",
                    "zaaktype_omschrijving",
                    "zaaktype_omschrijving_generiek",
                    "doel",
                    "aanleiding",
                    "toelichting",
                    "indicatie_intern_of_extern",
                    "trefwoorden",
                    "vertrouwelijkheidaanduiding",
                    "producten_of_diensten",
                    "verantwoordingsrelatie",
                )
            },
        ),
        (
            _("Behandeling"),
            {
                "fields": (
                    "handeling_initiator",
                    "onderwerp",
                    "handeling_behandelaar",
                    "doorlooptijd_behandeling",
                    "servicenorm_behandeling",
                ),
            },
        ),
        (
            _("Opschorten/verlengen"),
            {
                "fields": (
                    "opschorting_en_aanhouding_mogelijk",
                    "verlenging_mogelijk",
                    "verlengingstermijn",
                )
            },
        ),
        (_("Gemeentelijke selectielijst"), {"fields": ("selectielijst_procestype",)}),
        (
            _("Referentieproces"),
            {"fields": ("referentieproces_naam", "referentieproces_link")},
        ),
        (_("Publicatie"), {"fields": ("publicatie_indicatie", "publicatietekst")}),
        (_("Relaties"), {"fields": ("catalogus", "deelzaaktypen")}),
        (
            _("Geldigheid"),
            {
                "fields": (
                    "versiedatum",
                    "datum_begin_geldigheid",
                    "datum_einde_geldigheid",
                )
            },
        ),
    )
    raw_id_fields = ("catalogus", "deelzaaktypen")
    readonly_fields = ("versiedatum",)
    inlines = (
        ZaakTypenRelatieInline,
        StatusTypeInline,
        RolTypeInline,
        EigenschapInline,
        ResultaatTypeInline,
    )
    change_form_template = "admin/catalogi/change_form_zaaktype.html"
    exclude_copy_relation = ("zaak",)

    # For export mixin
    resource_name = "zaaktype"

    def get_related_objects(self, obj):
        resources = {}

        resources["ZaakType"] = [obj.pk]

        # M2M relations
        resources["BesluitType"] = list(obj.besluittypen.values_list("pk", flat=True))
        resources["InformatieObjectType"] = list(
            obj.informatieobjecttypen.values_list("pk", flat=True)
        )

        resources["ZaakTypeInformatieObjectType"] = list(
            obj.zaaktypeinformatieobjecttype_set.values_list("pk", flat=True)
        )

        # Resources with foreign keys to ZaakType
        fields = ["ResultaatType", "RolType", "StatusType", "Eigenschap"]
        for field in fields:
            model = apps.get_model("catalogi", field)
            resources[field] = list(
                model.objects.filter(zaaktype=obj).values_list("pk", flat=True)
            )

        resource_list = []
        id_list = []
        for resource, ids in resources.items():
            if ids:
                resource_list.append(resource)
                id_list.append(ids)

        return resource_list, id_list

    def _publish_validation_errors(self, obj):
        errors = []
        if (
            obj.besluittypen.filter(concept=True).exists()
            or obj.informatieobjecttypen.filter(concept=True).exists()
        ):
            errors.append(_("All related resources should be published"))
        return errors

    def get_object_actions(self, obj):
        return (
            link_to_related_objects(StatusType, obj),
            link_to_related_objects(RolType, obj),
            link_to_related_objects(Eigenschap, obj),
            link_to_related_objects(ResultaatType, obj),
            link_to_related_objects(ZaakTypenRelatie, obj),
        )

    def formfield_for_dbfield(self, db_field: Field, request: HttpRequest, **kwargs):
        if db_field.name == "selectielijst_procestype":
            return get_procestype_field(db_field, request, **kwargs)
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        obj.versiedatum = obj.datum_begin_geldigheid

        super().save_model(request, obj, form, change)

    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        # change form class in context
        adminform = context["adminform"]
        context["adminform"] = AdminForm(
            self.render_readonly,
            adminform.form,
            list(self.get_fieldsets(request, obj)),
            self.get_prepopulated_fields(request, obj)
            if add or self.has_change_permission(request, obj)
            else {},
            adminform.readonly_fields,
            model_admin=self,
        )
        return super().render_change_form(
            request, context, add=False, change=False, form_url="", obj=None
        )

    def render_readonly(self, field_name: str, value):
        if field_name == "producten_of_diensten":
            template = '<a href="{url}">{url}</a>'
            res = format_html(template, url=value)
            print("res=", res)
            return res

        return value
