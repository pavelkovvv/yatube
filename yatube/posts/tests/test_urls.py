from http import HTTPStatus
from django.test import TestCase, Client

from ..models import Post, Group, User
import yatube.settings as settings


class URLTestsPosts(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.create_group = Group.objects.create(
            title='Test group',
            slug='testslug',
            description='test descript'
        )
        self.create_post = Post.objects.create(
            text='Тестовый заголовок',
            author=self.user,
            group=self.create_group
        )

    def test_urls_uses_correct_template_all(self):
        '''URL-адрес использует соответствующий шаблон, который доступен
        всем'''

        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{self.create_group.slug}/',
            'posts/profile.html': f'/profile/{self.user.username}/',
            'posts/post_detail.html': f'/posts/{self.create_post.id}/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_404_page(self):
        '''Проверка запроса к несуществующей странице'''

        client_answer = {
            self.authorized_client: HTTPStatus.NOT_FOUND,
            self.guest_client: HTTPStatus.NOT_FOUND,
        }

        for client, answer in client_answer.items():
            with self.subTest(answer=answer):
                response = client.get('/unexisting_page/')
                self.assertEqual(response.status_code, answer)

        # Проверка, что страница 404 отдаёт кастомный шаблон
        settings.DEBUG = False
        response = self.authorized_client.get('/group/loooool/')

        self.assertTemplateUsed(response, 'core/404.html')
        settings.DEBUG = True

    def test_create_post(self):
        '''Проверка возможности создания поста только авторизованному
        пользователю'''

        client_answer = {
            self.authorized_client: HTTPStatus.OK,
            self.guest_client: HTTPStatus.FOUND,
        }

        for client, answer in client_answer.items():
            with self.subTest(answer=answer):
                response = client.get('/create/')
                self.assertEqual(response.status_code, answer)

    def test_post_edit(self):
        '''Проверка возможности изменения поста только его автору'''

        client_answer = {
            self.authorized_client: HTTPStatus.OK,
            self.guest_client: HTTPStatus.FOUND,
        }

        for client, answer in client_answer.items():
            with self.subTest(answer=answer):
                resp1 = client.get(
                    f'/posts/{self.create_post.id}/edit/')
                resp2 = client.get('/follow/')

                self.assertEqual(resp1.status_code, answer)
                self.assertEqual(resp2.status_code, answer)
