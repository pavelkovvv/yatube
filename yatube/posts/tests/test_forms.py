import shutil
import tempfile

from http import HTTPStatus
from django.test import Client, TestCase, override_settings
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from ..models import Group, Post, Comment, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsTestForms(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.guest_client = Client()
        self.group = Group.objects.create(
            title='Test group',
            slug='testslug',
            description='test descript'
        )
        self.post = Post.objects.create(
            text='Тестовый заголовок',
            author=self.user,
            group=self.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_form_create_post(self):
        """При отправке валидной формы со страницы posts:create_post
        создаётся новая запись в базе данных"""

        form_data = {
            'text': 'New post'
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        last_post = Post.objects.latest('pub_date')

        self.assertEqual(last_post.text, form_data['text'])
        self.assertEqual(last_post.author, self.user)
        self.assertIsNone(last_post.group)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_form_edit_post(self):
        """При отправке валидной формы со страницы posts:edit_post
        изменяется существующая запись в базе данных"""

        form_data = {
            'text': 'Edit post',
            'group': self.group.id
        }
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id':
                    self.post.id}),
            data=form_data,
            follow=True
        )
        need_post = Post.objects.get(id=self.post.id)

        self.assertEqual(need_post.text, form_data['text'])

        self.assertEqual(need_post.group, self.group)

    def test_form_create_post_guest_client(self):
        """При отправке валидной формы со страницы posts:create_post
        неавторизованным пользователем он будет перенаправлен на страницу
        входа, а новый пост не будет создан"""

        form_data = {
            'text': 'Новый пост неавторизованного пользователя',
            'group': self.group.id
        }

        quantity_posts = Post.objects.count()
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertEqual(quantity_posts, Post.objects.count())
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_PostForm_image(self):
        """Проверка, что при отправке поста с картинкой через форму PostForm
        создаётся запись в базе данных"""

        post_count = Post.objects.count()
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
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group.id,
            'image': uploaded,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post_image = Post.objects.first()

        self.assertEqual(post_image.image, 'posts/small.gif')
        self.assertEqual(Post.objects.count(), post_count + 1)

    def test_comment_in_context(self):
        """Проверка, что после успешной отправки комментарий появляется на
        странице поста"""

        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый пост',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id':
                    self.post.id}),
            data=form_data,
            follow=True
        )
        need_comment = Comment.objects.first()
        # Проверка, что верно создался объект в БД
        with self.subTest():
            self.assertRedirects(response, reverse(
                                 'posts:post_detail',
                                 kwargs={'post_id': self.post.pk}))
            self.assertEqual(comment_count + 1, Comment.objects.count())
            # Прошёлся по всему объекту комментария (после ревью обязательно
            # уберу этот коммент, просто так проще показать свою мысль, чем
            # спамить Вам личку)
            self.assertEqual(need_comment.text, form_data['text'])
            self.assertEqual(need_comment.post, self.post)
            self.assertEqual(need_comment.author, self.user)
