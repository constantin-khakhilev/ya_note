"""Тесты, касающиеся отображения контента.

Какие данные на каких страницах отображаются, какие при этом используются
шаблоны, как работает пагинатор.
"""
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestContent(TestCase):
    """Тестирование контента."""

    @classmethod
    def setUpTestData(cls):
        """Подготовка исходных данных."""
        # Создаём двух пользователей с разными именами:
        cls.author = User.objects.create(username='Автор заметки')
        cls.client_author = Client()
        cls.client_author.force_login(cls.author)
        cls.reader = User.objects.create(username='Другой пользователь')
        cls.client_reader = Client()
        cls.client_reader.force_login(cls.reader)
        # От имени одного пользователя создаём заметку:
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='slug',
            author=cls.author
        )
        cls.LIST_URL = reverse('notes:list')
        cls.ADD_URL = reverse('notes:add')
        cls.EDIT_URL = reverse('notes:edit', args=(cls.note.slug,))

    def test_note_in_list_for_author(self):
        """Отдельная заметка передаётся на страницу со списком заметок в
        списке object_list в словаре context.
        """
        response = self.client_author.get(self.LIST_URL)
        object_list = response.context['object_list']
        self.assertIn(self.note, object_list)

    def test_note_not_in_list_for_another_user(self):
        """В список заметок одного пользователя не попадают заметки другого
        пользователя.
        """
        response = self.client_reader.get(self.LIST_URL)
        object_list = response.context['object_list']
        self.assertNotIn(self.note, object_list)

    def test_pages_contains_form(self):
        """Есть ли форма создания или редактирования в контексте."""
        urls = (
            self.ADD_URL,
            self.EDIT_URL,
        )
        # Запрашиваем страницу создания заметки:
        for url in urls:
            response = self.client_author.get(url)
            self.assertIn('form', response.context)
