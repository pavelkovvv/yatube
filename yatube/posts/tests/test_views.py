import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.conf import settings
from django import forms

from ..models import Post, Group, User
from ..utils import QUANTITY_POSTS

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsTestPosts(TestCase):
    TOTAL_POSTS_IN_TESTS = 15

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.create_group0 = Group.objects.create(
            title='Test group 0',
            slug='testslug0',
            description='test descript'
        )
        self.create_group1 = Group.objects.create(
            title='Test group 1',
            slug='testslug1',
            description='test descript'
        )
        Post.objects.bulk_create([
            Post(text=f'Тестовый заголовок № {i}',
                 author=self.user,
                 group=self.create_group0)
            for i in range(self.TOTAL_POSTS_IN_TESTS)
        ])
        self.first_post_from_db = Post.objects.get(id=1)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон"""

        cache.clear()
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse('posts:group_list',
                                             kwargs={'slug':
                                                     self.create_group0.slug}),
            'posts/profile.html': reverse('posts:profile',
                                          kwargs={'username':
                                                  self.user.username}),
            'posts/post_detail.html': reverse('posts:post_detail',
                                              kwargs={'post_id':
                                                      self.first_post_from_db.
                                                      id}),
            'posts/create_post.html': [reverse('posts:post_edit',
                                               kwargs={'post_id':
                                                       self.first_post_from_db.
                                                       id}),
                                       reverse('posts:post_create')],
            'posts/follow.html': reverse('posts:follow_index'),
        }
        for template, reverse_name in templates_pages_names.items():
            if template == 'posts/create_post.html':
                with self.subTest(reverse_name=reverse_name):
                    for i in range(
                            len(templates_pages_names[
                                'posts/create_post.html'])):
                        response = self.authorized_client.get(reverse_name[i])
                        self.assertTemplateUsed(response, template)
            else:
                with self.subTest(reverse_name=reverse_name):
                    response = self.authorized_client.get(reverse_name)
                    self.assertTemplateUsed(response, template)

    def test_correct_index_context(self):
        """Шаблон posts/index.html сформирован с правильным контекстом"""

        cache.clear()
        post_list = Post.objects.all()
        response = self.authorized_client.get(reverse('posts:index'))
        # Проверяем все посты первой страницы (на странице 10 постов)
        self.assertIn('page_obj', response.context)
        for i in range(QUANTITY_POSTS):
            with self.subTest():
                self.assertEqual(response.context['page_obj'][i], post_list[i])

    def test_correct_group_list_context(self):
        """Шаблон posts/group_list.html сформирован с правильным контекстом"""

        group = Group.objects.all()[0]
        response = self.authorized_client.get(reverse('posts:group_list',
                                              kwargs={'slug':
                                                      self.create_group0.
                                                      slug}))
        self.assertIn('page_obj', response.context)
        self.assertEqual(response.context['group'], group)

    def test_correct_profile_context(self):
        """Шаблон posts/profile.html сформирован с правильным контекстом"""

        post_users = Post.objects.filter(author=self.user)
        resp = self.authorized_client.get(reverse('posts:profile',
                                          kwargs={'username':
                                                  self.user.username}))
        # Проверяем все посты и автора первой страницы (на странице 10 постов)
        self.assertEqual(resp.context['author'], self.user)
        for i in range(QUANTITY_POSTS):
            with self.subTest():
                self.assertEqual(resp.context['page_obj'][i].author, self.user)
                self.assertEqual(resp.context['page_obj'][i], post_users[i])

    def test_correct_post_detail_context(self):
        """Шаблон posts/post_detail.html сформирован с правильным контекстом"""

        resp = self.authorized_client.get(reverse('posts:post_detail',
                                                  kwargs={'post_id':
                                                          self.
                                                          first_post_from_db.
                                                          id}))

        self.assertEqual(resp.context['post'], self.first_post_from_db)

    def test_correct_create_post_context(self):
        """Шаблон posts/create_post.html сформирован с правильным контекстом"""

        resp = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                self.assertIn('form', resp.context)
                form_field = resp.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_correct_posts_edit_context(self):
        """Шаблон posts:post_edit сформирован с правильным контекстом"""

        resp = self.authorized_client.get(reverse('posts:post_edit',
                                                  kwargs={'post_id':
                                                          self.
                                                          first_post_from_db.
                                                          id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                self.assertIn('form', resp.context)
                form_field = resp.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_paginator(self):
        """Проверяем корректную работу паджинатора в шаблонах:
        posts/index.html, posts/group_list.html и posts/profile.html"""

        templates_for_check = (reverse('posts:index'),
                               (reverse('posts:group_list',
                                        kwargs={'slug':
                                                self.create_group0.slug})),
                               (reverse('posts:profile',
                                        kwargs={'username':
                                                self.user.username})))
        QUANTITY_POSTS_ON_SECOND_PAGE = (self.TOTAL_POSTS_IN_TESTS
                                         - QUANTITY_POSTS)
        cache.clear()

        with self.subTest():
            for i in templates_for_check:
                # Проверка первой страницы
                response = self.authorized_client.get(i)
                self.assertEqual(len(response.context['page_obj']),
                                 QUANTITY_POSTS)
                # Проверка второй страницы
                response = self.authorized_client.get(i + '?page=2')
                self.assertEqual(len(response.context['page_obj']),
                                 QUANTITY_POSTS_ON_SECOND_PAGE)

    def test_z_additional_check(self):
        """Проверка, что созданный пост не попал в группу, для которой
        не был предназначен"""

        new_post = Post.objects.create(
            text='Ложный пост',
            author=self.user,
            group=self.create_group1
        )
        resp = self.authorized_client.get(reverse('posts:group_list',
                                          kwargs={'slug':
                                                  self.create_group0.slug}))
        self.assertNotIn(new_post, resp.context['page_obj'])

    def test_image_context(self):
        """Проверка, что при выводе поста с картинкой изображение передаётся
        в словаре context"""

        cache.clear()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        post_with_image = Post.objects.create(
            text='Я пост с картинкой',
            author=self.user,
            group=self.create_group0,
            image=uploaded,
        )
        templates_for_check = {
            reverse('posts:index'): 'page_obj',
            reverse('posts:group_list', kwargs={'slug':
                    self.create_group0.slug}): 'page_obj',
            reverse('posts:post_detail', kwargs={'post_id':
                    post_with_image.id}): 'post'
        }

        for address, form in templates_for_check.items():
            with self.subTest():
                response = self.authorized_client.get(address)
                if form == 'page_obj':
                    self.assertEqual(response.context[form][0].image,
                                     'posts/small.gif')
                else:
                    self.assertEqual(response.context[form].image,
                                     'posts/small.gif')

    def test_comment_only_authorized_user(self):
        """Проверка, что комментировать посты может только авторизованный
        пользователь"""

        post_for_comment = Post.objects.create(
            text='Post without comments^(',
            author=self.user,
            group=self.create_group0,
        )
        resp = self.guest_client.get(reverse('posts:add_comment', kwargs={
            'post_id': post_for_comment.id}))
        redir_url = f'/auth/login/?next=/posts/{post_for_comment.id}/comment/'

        self.assertRedirects(resp, redir_url)

    def test_caches(self):
        """Проверка работы кеша главной страницы"""

        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='test_new_post',
            author=self.user,
        )
        response_old = self.authorized_client.get(reverse('posts:index'))
        old_posts = response_old.content

        self.assertEqual(old_posts, posts)

        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        new_posts = response_new.content

        self.assertNotEqual(old_posts, new_posts)


class ViewsTestPostsFollow(TestCase):
    def setUp(self):
        self.guest_client = Client()
        # Создание 1 пользователя
        self.user1 = User.objects.create_user(username='Tester1')
        self.auth_user1 = Client()
        self.auth_user1.force_login(self.user1)
        # Создание 2 пользователя
        self.user2 = User.objects.create_user(username='Tester2')
        self.auth_user2 = Client()
        self.auth_user2.force_login(self.user2)
        # Создание 3 пользователя
        self.user3 = User.objects.create_user(username='Tester3')
        self.auth_user3 = Client()
        self.auth_user3.force_login(self.user3)
        # Создадим 6 постов для первого пользователя
        self.POSTS_FOR_FIRST_USER = 6
        Post.objects.bulk_create([
            Post(text=f'Тестовый заголовок № {i} для 1 юзера',
                 author=self.user1)
            for i in range(self.POSTS_FOR_FIRST_USER)
        ])
        # Создадим 3 поста для второго пользователя
        self.POSTS_FOR_SECOND_USER = 3
        Post.objects.bulk_create([
            Post(text=f'Тестовый заголовок № {i} для 2 юзера',
                 author=self.user2)
            for i in range(self.POSTS_FOR_SECOND_USER)
        ])
        # Создадим 2 поста для третьего пользователя
        self.POSTS_FOR_THIRD_USER = 2
        Post.objects.bulk_create([
            Post(text=f'Тестовый заголовок № {i} для 3 юзера',
                 author=self.user3)
            for i in range(self.POSTS_FOR_THIRD_USER)
        ])

    def test_follow(self):
        """Проверка, что авторизованный пользователь может подписываться на
        других пользователей и удалять их из подписок"""

        # Смоделируем ситуацию, что первый автор подписался на второго автора
        # Сравним кол-во постов второго автора с итоговым кол-вом постов
        # Первого автора на странице его подписок
        self.auth_user1.get(reverse('posts:profile_follow',
                                    kwargs={'username': self.user2.username}))
        resp2 = self.auth_user1.get(reverse('posts:follow_index'))
        after_test = len(resp2.context['page_obj'])

        self.assertEqual(self.POSTS_FOR_SECOND_USER, after_test)

        # Возьмём значение кол-ва подписок после подписки первого автора на
        # второго, затем отпишемся и сравним значения
        self.auth_user1.get(reverse('posts:profile_unfollow',
                                    kwargs={'username': self.user2.username}))
        resp3 = self.auth_user1.get(reverse('posts:follow_index'))
        after_unfollow = len(resp3.context['page_obj'])

        self.assertNotEqual(after_unfollow, after_test)

    def test_new_post_follow(self):
        """Проверка, что новая запись пользователя появляется в ленте тех, кто
        на него подписан и не появляется в ленте тех, кто не подписан"""

    # Проверим, что новая запись появляется в ленте тех, кто на него подписан
        self.auth_user1.get(reverse('posts:profile_follow',
                                    kwargs={'username': self.user2.username}))
        resp1 = self.auth_user1.get(reverse('posts:follow_index'))
        len_test1 = len(resp1.context['page_obj'])
        Post.objects.create(
            text='textpost',
            author=self.user2
        )
        resp2 = self.auth_user1.get(reverse('posts:follow_index'))
        len_test2 = len(resp2.context['page_obj'])

        self.assertEqual(len_test1 + 1, len_test2)
        param_value = {
            'text': 'textpost',
            'author': self.user2,
        }
        with self.subTest():
            response = resp2.context['page_obj'][0]
            self.assertEqual(response.text, param_value['text'])
            self.assertEqual(response.author, param_value['author'])

    # Проверим, что новая запись не появляется в ленте тех, кто не подписан

        resp3 = self.auth_user3.get(reverse('posts:follow_index'))
        len_test3 = len(resp3.context['page_obj'])

        self.assertNotEqual(len_test3, len_test2)
