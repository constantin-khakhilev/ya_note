"""Тесты доступности конкретных эндпоинтов, проверка редиректов.

Кодов ответа, которые возвращают страницы, тестирование доступа для
авторизованных или анонимных пользователей.
"""

from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):
    """Тестирование маршрутов."""

    @classmethod
    def setUpTestData(cls):
        """Подготовка исходных данных."""
        # Создаём двух пользователей с разными именами и логинимся:
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
        # Адреса страниц:
        cls.HOME_URL = reverse('notes:home')
        cls.LOGIN_URL = reverse('users:login')
        cls.LOGOUT_URL = reverse('users:logout')
        cls.SIGNUP_URL = reverse('users:signup')
        cls.LIST_URL = reverse('notes:list')
        cls.SUCCESS_URL = reverse('notes:success')
        cls.ADD_URL = reverse('notes:add')
        cls.EDIT_URL = reverse('notes:edit', args=(cls.note.slug,))
        cls.DETAIL_URL = reverse('notes:detail', args=(cls.note.slug,))
        cls.DELETE_URL = reverse('notes:delete', args=(cls.note.slug,))

    def test_pages_availability(self):
        """Проверка доступности до страниц анонимным пользователем."""
        # Создаём набор тестовых данных - кортеж кортежей.
        # Каждый вложенный кортеж содержит два элемента:
        # имя пути и позиционные аргументы для функции reverse().
        urls = (
            self.HOME_URL,
            self.LOGIN_URL,
            self.LOGOUT_URL,
            self.SIGNUP_URL,
        )
        for url in urls:
            with self.subTest(url=url):
                # Получаем ответ.
                response = self.client.get(url)
                # Проверяем, что код ответа равен статусу OK (он же 200).
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_note_detail_edit_and_delete(self):
        """Проверка страниц отображения, редактирования и удаления заметки."""
        urls = (
            self.EDIT_URL,
            self.DETAIL_URL,
            self.DELETE_URL,
        )
        users_statuses = (
            (self.client_author, HTTPStatus.OK),
            (self.client_reader, HTTPStatus.NOT_FOUND),
        )
        for client, status in users_statuses:
            # Для каждой пары "пользователь - ожидаемый ответ"
            # перебираем имена тестируемых страниц:
            for url in urls:
                with self.subTest(client=client, url=url):
                    response = client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """Проверка редиректов от анонимных пользователей."""
        urls = (
            self.LIST_URL,
            self.SUCCESS_URL,
            self.ADD_URL,
            self.EDIT_URL,
            self.DETAIL_URL,
            self.DELETE_URL,
        )
        for url in urls:
            with self.subTest(url=url):
                redirect_url = f'{self.LOGIN_URL}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)

    def test_list_notes(self):
        """Проверка списка заметок для авторизованного пользователя."""
        urls = (
            self.LIST_URL,
            self.SUCCESS_URL,
            self.ADD_URL,
        )
        for url in urls:
            response = self.client_author.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)
