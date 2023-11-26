"""Тестирование бизнес-логики приложения.

Как обрабатываются те или иные формы, разрешено ли создание объектов с
неуникальными полями, как работает специфичная логика конкретного приложения.
"""

from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):
    """Тестирование создания заметки."""

    NOTE_TITLE = 'Заголовок заметки'
    NOTE_TEXT = 'Текст заметки'
    NOTE_SLUG = 'note_slug'
    NOTE_SLUG_TRANSLITERATED = 'zagolovok-zametki'

    @classmethod
    def setUpTestData(cls):
        """Подготовка исходных данных."""
        # Создаём пользователя и клиент, логинимся в клиенте.
        cls.user = User.objects.create(username='Лев Толстой')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        # Данные для POST-запроса при создании заметки.
        cls.form_data = {
            'title': cls.NOTE_TITLE,
            'text': cls.NOTE_TEXT,
            'slug': cls.NOTE_SLUG
        }
        # Адреса страниц:
        cls.ADD_URL = reverse('notes:add')
        cls.SUCCESS_URL = reverse('notes:success')

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создавать заметку."""
        notes_count_start = Note.objects.count()
        # Совершаем запрос от анонимного клиента, в POST-запросе отправляем
        # предварительно подготовленные данные формы с текстом заметки.
        self.client.post(self.ADD_URL, data=self.form_data)
        notes_count_finish = Note.objects.count()
        self.assertEqual(notes_count_finish - notes_count_start, 0)

    def test_user_can_create_note(self):
        """Авторизованный пользователь может создать заметку."""
        notes_count_start = Note.objects.count()
        # Совершаем запрос через авторизованный клиент.
        response = self.auth_client.post(self.ADD_URL, data=self.form_data)
        # Проверяем, что редирект привёл к странице "Успешно".
        self.assertRedirects(response, self.SUCCESS_URL)
        notes_count_finish = Note.objects.count()
        self.assertEqual(notes_count_finish - notes_count_start, 1)
        # Получаем объект заметки из базы.
        note = Note.objects.get()
        # Проверяем, что все атрибуты заметки совпадают с ожидаемыми.
        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.slug, self.NOTE_SLUG)
        self.assertEqual(note.author, self.user)

    def test_user_cant_create_two_notes_with_same_slug(self):
        """Пользователь не может создать 2 заметки с одинаковым slug."""
        notes_count_start = Note.objects.count()
        # Создаём первую заметку.
        # Отправляем запрос через авторизованный клиент.
        response = self.auth_client.post(self.ADD_URL, data=self.form_data)
        # Убедимся, что заметка была создана.
        notes_count_finish = Note.objects.count()
        self.assertEqual(notes_count_finish - notes_count_start, 1)
        # Создаём вторую заметку.
        # Отправляем запрос через авторизованный клиент.
        response = self.auth_client.post(self.ADD_URL, data=self.form_data)
        # Проверяем, есть ли в ответе ошибка формы.
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=self.form_data['slug'] + WARNING
        )
        # Дополнительно убедимся, что заметка не была создана.
        notes_count_finish = Note.objects.count()
        self.assertEqual(notes_count_finish - notes_count_start, 1)

    def test_create_translate_slug_from_title(self):
        """Создание slug из транслитерированного названия заметки."""
        notes_count_start = Note.objects.count()
        # Создаём заметку не передавая slug.
        self.form_data.pop('slug')
        self.auth_client.post(self.ADD_URL, data=self.form_data)
        notes_count_finish = Note.objects.count()
        self.assertEqual(notes_count_finish - notes_count_start, 1)
        # Получаем объект заметки из базы.
        note = Note.objects.get()
        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.slug, self.NOTE_SLUG_TRANSLITERATED)


class TestNoteEditDelete(TestCase):
    """Проверка удаления и редактирования заметок."""

    # Тексты для заметок.
    NOTE_TITLE = 'Заголовок заметки'
    NOTE_TEXT = 'Текст заметки'
    NOTE_SLUG = 'note_slug'
    NEW_NOTE_TITLE = 'Обновлённый заголовок заметки'
    NEW_NOTE_TEXT = 'Обновлённый текст заметки'
    NEW_NOTE_SLUG = 'new_note_slug'

    @classmethod
    def setUpTestData(cls):
        """Подготовка исходных данных."""
        # Создаём пользователя - автора заметки.
        cls.author = User.objects.create(username='Автор заметки')
        # Создаём клиент для пользователя-автора.
        cls.author_client = Client()
        # "Логиним" пользователя в клиенте.
        cls.author_client.force_login(cls.author)
        # Делаем всё то же самое для пользователя-читателя.
        cls.reader = User.objects.create(username='Другой пользователь')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        # Создаём заметку в БД.
        cls.note = Note.objects.create(
            title=cls.NOTE_TITLE,
            text=cls.NOTE_TEXT,
            slug=cls.NOTE_SLUG,
            author=cls.author
        )
        # Формируем данные для POST-запроса по обновлению заметки.
        cls.form_data = {
            'title': cls.NEW_NOTE_TITLE,
            'text': cls.NEW_NOTE_TEXT,
            'slug': cls.NEW_NOTE_SLUG
        }
        # Адреса страниц:
        cls.EDIT_URL = reverse('notes:edit', args=(cls.note.slug,))
        cls.DELETE_URL = reverse('notes:delete', args=(cls.note.slug,))
        cls.SUCCESS_URL = reverse('notes:success')

    def test_author_can_delete_note(self):
        """Проверка удаления заметки автором."""
        notes_count_start = Note.objects.count()
        # От имени автора заметки отправляем DELETE-запрос на удаление.
        response = self.author_client.delete(self.DELETE_URL)
        # Проверяем, что редирект привёл к странице "Успешно".
        # Заодно проверим статус-коды ответов.
        self.assertRedirects(response, self.SUCCESS_URL)
        notes_count_finish = Note.objects.count()
        self.assertEqual(notes_count_start - notes_count_finish, 1)

    def test_user_cant_delete_note_of_another_user(self):
        """Проверка удаления заметки другим пользователем."""
        notes_count_start = Note.objects.count()
        # Выполняем запрос на удаление от другого пользователя.
        response = self.reader_client.delete(self.DELETE_URL)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count_finish = Note.objects.count()
        self.assertEqual(notes_count_start - notes_count_finish, 0)

    def test_author_can_edit_note(self):
        """Проверка редактирования заметки автором."""
        # Выполняем запрос на редактирование от имени автора заметки.
        response = self.author_client.post(self.EDIT_URL, data=self.form_data)
        # Проверяем, что сработал редирект.
        self.assertRedirects(response, self.SUCCESS_URL)
        # Обновляем объект заметки.
        self.note.refresh_from_db()
        # Проверяем, что все атрибуты заметки соответствует обновленной.
        self.assertEqual(self.note.title, self.NEW_NOTE_TITLE)
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)
        self.assertEqual(self.note.slug, self.NEW_NOTE_SLUG)

    def test_user_cant_edit_note_of_another_user(self):
        """Проверка редактирования заметки другим пользователем."""
        # Выполняем запрос на редактирование от имени другого пользователя.
        response = self.reader_client.post(self.EDIT_URL, data=self.form_data)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Обновляем объект заметки.
        self.note.refresh_from_db()
        # Проверяем, что все атрибуты заметки остались теми же, что и были.
        self.assertEqual(self.note.title, self.NOTE_TITLE)
        self.assertEqual(self.note.text, self.NOTE_TEXT)
        self.assertEqual(self.note.slug, self.NOTE_SLUG)
