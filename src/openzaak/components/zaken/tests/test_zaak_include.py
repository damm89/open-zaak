# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2022 Dimpact
import json

from django.test import tag

import requests_mock
from rest_framework import status
from rest_framework.test import APITestCase
from vng_api_common.tests import reverse

from openzaak.components.catalogi.tests.factories import (
    StatusTypeFactory,
    ZaakTypeFactory,
)
from openzaak.components.catalogi.tests.factories.catalogus import CatalogusFactory
from openzaak.utils.tests import JWTAuthMixin

from .factories import ZaakFactory
from .utils import ZAAK_READ_KWARGS, get_catalogus_response, get_zaaktype_response


@tag("include")
class ZakenIncludeTests(JWTAuthMixin, APITestCase):
    heeft_alle_autorisaties = True
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.catalogus = CatalogusFactory.create()
        cls.zaaktype = ZaakTypeFactory.create(concept=False, catalogus=cls.catalogus)
        cls.zaaktype_url = reverse(cls.zaaktype)
        cls.statustype = StatusTypeFactory.create(zaaktype=cls.zaaktype)
        cls.statustype_url = reverse(cls.statustype)
        cls.statustype2 = StatusTypeFactory.create(zaaktype=cls.zaaktype)
        cls.statustype2_url = reverse(cls.statustype2)

        super().setUpTestData()

    def test_zaak_list_include(self):
        """
        Test if related resources that are in the local database can be included
        """
        ZaakFactory.create(zaaktype=self.zaaktype)

        url = reverse("zaak-list")

        zaaktype_data = json.loads(self.client.get(reverse(self.zaaktype)).content)["data"]

        response = self.client.get(url, {"include": "zaaktype"}, **ZAAK_READ_KWARGS,)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # `response.data` does not generate the rendered response
        data = json.loads(response.content)

        self.assertIn("inclusions", data)
        self.assertDictEqual(data["inclusions"], {"catalogi:zaaktype": [zaaktype_data]})


@tag("include")
class ZakenExternalIncludeTests(JWTAuthMixin, APITestCase):
    heeft_alle_autorisaties = True
    maxDiff = None

    def test_zaak_list_include(self):
        """
        Test if related resources that are external can be included
        """
        catalogus = "https://externe.catalogus.nl/api/v1/catalogussen/1c8e36be-338c-4c07-ac5e-1adf55bec04a"
        zaaktype = "https://externe.catalogus.nl/api/v1/zaaktypen/b71f72ef-198d-44d8-af64-ae1932df830a"
        zaaktype_data = get_zaaktype_response(catalogus, zaaktype)
        catalogus_data = get_catalogus_response(catalogus, zaaktype)

        ZaakFactory.create(zaaktype=zaaktype)

        url = reverse("zaak-list")

        with requests_mock.Mocker(real_http=True) as m:
            m.register_uri(
                "GET", zaaktype, json=zaaktype_data,
            )
            m.register_uri(
                "GET", catalogus, json=catalogus_data,
            )
            response = self.client.get(
                url, {"include": "zaaktype"}, **ZAAK_READ_KWARGS,
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # `response.data` does not generate the rendered response
        data = json.loads(response.content)

        self.assertIn("inclusions", data)
        self.assertDictEqual(data["inclusions"], {"catalogi:zaaktype": [zaaktype_data]})
