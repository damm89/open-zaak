from collections import defaultdict
from typing import Any, Dict, List

from django import forms
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView

from vng_api_common.authorizations.models import Applicatie, Autorisatie
from vng_api_common.constants import ComponentTypes

from openzaak.components.catalogi.models import (
    BesluitType,
    Catalogus,
    InformatieObjectType,
    ZaakType,
)

from .admin_serializers import CatalogusSerializer
from .constants import RelatedTypeSelectionMethods
from .forms import (
    COMPONENT_TO_PREFIXES_MAP,
    AutorisatieFormSet,
    VertrouwelijkheidsAanduiding,
    get_scope_choices,
)
from .utils import get_related_object


def get_form_data(form: forms.Form) -> Dict[str, Dict]:
    """
    Serialize the form data and errors for the frontend.
    """
    errors = (
        {
            field: [{"msg": error.message, "code": error.code} for error in _errors]
            for field, _errors in form.errors.as_data().items()
        }
        if form.is_bound
        else {}
    )

    values = {field.name: field.value() for field in form}
    return {
        "errors": errors,
        "values": values,
    }


def get_initial_for_component(
    component: str, autorisaties: List[Autorisatie]
) -> List[Dict[str, Any]]:
    if component not in [ComponentTypes.zrc, ComponentTypes.drc, ComponentTypes.brc]:
        return []

    related_objs = {
        autorisatie.pk: get_related_object(autorisatie).id
        for autorisatie in autorisaties
    }

    initial = []

    if component == ComponentTypes.zrc:
        zaaktype_ids = set(ZaakType.objects.values_list("id", flat=True))

        grouped_by_va = defaultdict(list)
        for autorisatie in autorisaties:
            grouped_by_va[autorisatie.max_vertrouwelijkheidaanduiding].append(
                autorisatie
            )

        for va, _autorisaties in grouped_by_va.items():
            _initial = {"vertrouwelijkheidaanduiding": va}
            relevant_ids = {
                related_objs[autorisatie.pk] for autorisatie in _autorisaties
            }

            if zaaktype_ids == relevant_ids:
                _initial[
                    "related_type_selection"
                ] = RelatedTypeSelectionMethods.all_current
            else:
                _initial.update(
                    {
                        "related_type_selection": RelatedTypeSelectionMethods.manual_select,
                        "zaaktypen": relevant_ids,
                    }
                )
            initial.append(_initial)

    elif component == ComponentTypes.drc:
        informatieobjecttype_ids = set(
            InformatieObjectType.objects.values_list("id", flat=True)
        )

        grouped_by_va = defaultdict(list)
        for autorisatie in autorisaties:
            grouped_by_va[autorisatie.max_vertrouwelijkheidaanduiding].append(
                autorisatie
            )

        for va, _autorisaties in grouped_by_va.items():
            _initial = {"vertrouwelijkheidaanduiding": va}
            relevant_ids = {
                related_objs[autorisatie.pk] for autorisatie in _autorisaties
            }

            if informatieobjecttype_ids == relevant_ids:
                _initial[
                    "related_type_selection"
                ] = RelatedTypeSelectionMethods.all_current
            else:
                _initial.update(
                    {
                        "related_type_selection": RelatedTypeSelectionMethods.manual_select,
                        "informatieobjecttypen": relevant_ids,
                    }
                )
            initial.append(_initial)

    elif component == ComponentTypes.brc:
        besluittype_ids = set(BesluitType.objects.values_list("id", flat=True))
        relevant_ids = set(related_objs.values())

        _initial = {}
        if besluittype_ids == relevant_ids:
            _initial["related_type_selection"] = RelatedTypeSelectionMethods.all_current
        else:
            _initial.update(
                {
                    "related_type_selection": RelatedTypeSelectionMethods.manual_select,
                    "besluittypen": relevant_ids,
                }
            )
        initial.append(_initial)

    return initial


def get_initial(applicatie: Applicatie) -> List[Dict[str, Any]]:
    """
    Figure out the initial data for the formset, showing existing config.

    We group applicatie autorisaties bij (component, scopes) and evaluate
    if this constitutes one of the "special" options. If so, we can provide
    this information to the form, presenting it much more condensed to the
    end user.
    """
    initial = []

    grouped = defaultdict(list)
    autorisaties = applicatie.autorisaties.all()
    for autorisatie in autorisaties:
        key = (
            autorisatie.component,
            tuple(sorted(autorisatie.scopes)),
        )
        grouped[key].append(autorisatie)

    for (component, _scopes), _autorisaties in grouped.items():
        component_initial = get_initial_for_component(component, _autorisaties)

        initial += [
            {"component": component, "scopes": list(_scopes), **_initial}
            for _initial in component_initial
        ]

    return initial


class AutorisatiesView(DetailView):
    model = Applicatie
    template_name = "admin/autorisaties/applicatie_autorisaties.html"
    pk_url_kwarg = "object_id"
    # set these on the .as_viev(...) call
    admin_site = None
    model_admin = None

    # perform permission checks
    def dispatch(self, request, *args, **kwargs):
        assert self.admin_site
        assert self.model_admin

        applicatie = self.get_object()
        if not self.model_admin.has_change_permission(request, applicatie):
            raise PermissionDenied()

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = applicatie = self.get_object()
        formset = self.get_formset()

        if formset.is_valid():
            formset.save()

            # TODO: send out notification to NRC!

            return redirect(
                "admin:authorizations_applicatie_change", object_id=applicatie.pk
            )

        context = self.get_context_data(formset=formset)
        return self.render_to_response(context)

    def get_formset(self):
        initial = get_initial(self.object)
        print(initial)
        data = self.request.POST if self.request.method == "POST" else None
        return AutorisatieFormSet(
            data=data, initial=initial, applicatie=self.object, request=self.request
        )

    def get_context_data(self, **kwargs):
        formset = kwargs.pop("formset", self.get_formset())
        kwargs["formset"] = formset

        context = super().get_context_data(**kwargs)

        catalogi = Catalogus.objects.prefetch_related(
            "zaaktype_set", "informatieobjecttype_set", "besluittype_set",
        )

        context.update(self.admin_site.each_context(self.request))
        context.update(
            {
                "opts": Applicatie._meta,
                "original": self.get_object(),
                "title": _("beheer autorisaties"),
                "is_popup": False,
                "formset_config": {
                    "prefix": formset.prefix,
                    "extra": formset.extra,
                    **{
                        field.name: int(field.value())
                        for field in formset.management_form
                    },
                },
                "scope_choices": get_scope_choices(),
                "COMPONENTS_TO_PREFIXES_MAP": COMPONENT_TO_PREFIXES_MAP,
                "RELATED_TYPE_SELECTION_METHODS": RelatedTypeSelectionMethods.choices,
                "VA_CHOICES": VertrouwelijkheidsAanduiding.choices,
                "catalogi": CatalogusSerializer(
                    catalogi, read_only=True, many=True
                ).data,
                "formdata": [get_form_data(form) for form in formset],
            }
        )

        return context
