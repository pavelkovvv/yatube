from django.test import TestCase

from ..models import Group, Post, User


class TestPostGroup(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group_str = Group.objects.create(
            title='Тестовый заголовок 1',
            slug='test1',
            description='Описание теста 1',
        )

        cls.post_str = Post.objects.create(
            text='Этот текст создан для актуальности проверки поста',
            author=cls.user,

        )

    def test_str_group(self):
        """Проверяем, что у модели Group корректно работает __str__"""
        group = TestPostGroup.group_str
        expected_group_str = group.title
        self.assertEqual(expected_group_str, str(group))

    def test_str_post(self):
        """Проверяем, что у модели Post корректно работает __str__"""
        post = TestPostGroup.post_str
        expected_post_str = post.text[:15]
        self.assertEqual(expected_post_str, str(post))

    def test_verbose_name(self):

        post = TestPostGroup.post_str
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_help_text(self):

        post = TestPostGroup.post_str
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу, к которой будет относиться пост'
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)
