# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2021 Dimpact
from django.urls import reverse

from django_webtest import WebTest

from openzaak.utils.constants import COMPONENT_MAPPING
from openzaak.utils.tests import AdminTestMixin

from .factories import InternalServiceFactory


class ConfigDetailTests(AdminTestMixin, WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        for api_type in COMPONENT_MAPPING.values():
            InternalServiceFactory.create(api_type=api_type)

    def setUp(self):
        super().setUp()
        self.app.set_user(self.user)

    def test_get_detail_page(self):
        url = reverse("config:config-detail")

        detail_page = self.app.get(url)

        self.assertEqual(detail_page.status_code, 200)
