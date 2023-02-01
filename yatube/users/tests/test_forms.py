from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UsersTestsForm(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_quantity_users(self):
        """Проверим, что при заполнении формы users:signup создаётся
        новый профиль"""

        first_count = User.objects.count()
        form_data = {
            'username': 'pavlelkovvvv',
            'email': 'pavelkov@mail.ru',
            'password1': 'passweef1112',
            'password2': 'passweef1112'
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )

        self.assertEqual(User.objects.count(), first_count + 1)
        self.assertEqual(response.status_code, 200)
