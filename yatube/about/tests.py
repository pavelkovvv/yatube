from http import HTTPStatus
from django.test import TestCase, Client


class URLTestsAbout(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.urls_and_templates = {
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/',
        }

    def test_urls_uses_correcrt_template(self):
        """Проверка доступности адресов /about/ и /tech/"""

        for address in self.urls_and_templates.values():
            response = self.guest_client.get(address)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_template_uses_correcrt_urls(self):
        """Проверка шаблона для адресов /about/ и /tech/"""

        for template, address in self.urls_and_templates.items():
            response = self.guest_client.get(address)
            self.assertTemplateUsed(response, template)
