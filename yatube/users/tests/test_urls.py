from django.contrib.auth import get_user_model
from django.test import TestCase, Client

User = get_user_model()


class URLTestsUsers(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template_all_users(self):
        '''URL-адрес использует соответствующий шаблон, который доступен
        всем'''

        templates_url_names = {
            'users/logged_out.html': '/auth/logout/',
            'users/signup.html': '/auth/signup/',
            'users/login.html': '/auth/login/',
            'users/password_reset_form.html': '/auth/password_reset/',
            'users/password_reset_done.html': '/auth/password_reset/done/',
            'users/password_reset_complete.html': '/auth/reset/done/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_auth_users(self):
        '''URL-адрес использует соответствующий шаблон, который доступен
        только зарегистрированным пользователям'''

        templates_url_names = {
            'users/password_change_form.html': '/auth/password_change/',
            'users/password_change_done.html': '/auth/password_change/done/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
