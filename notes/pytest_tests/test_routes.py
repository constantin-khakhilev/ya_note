"""Тесты доступности конкретных эндпоинтов, проверка редиректов.

Кодов ответа, которые возвращают страницы, тестирование доступа для
авторизованных или анонимных пользователей.
"""
from http import HTTPStatus

import pytest  # Для использования маркеров нужно импортировать модуль pytest.
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from notes.models import Note


@pytest.mark.parametrize(
    'name',  # Имя параметра функции.
    # Значения, которые будут передаваться в name.
    ('notes:home', 'users:login', 'users:logout', 'users:signup')
)
# Указываем имя изменяемого параметра в сигнатуре теста.
def test_pages_availability_for_anonymous_user(client, name):
    """Доступы до страниц анонимному пользователю."""
    url = reverse(name)  # Получаем ссылку на нужный адрес.
    response = client.get(url)  # Выполняем запрос.
    assert response.status_code == HTTPStatus.OK


# Добавляем к тесту ещё один декоратор parametrize; в его параметры
# нужно передать фикстуры-клиенты и ожидаемый код ответа для каждого клиента.
@pytest.mark.parametrize(
    # parametrized_client - название параметра,
    # в который будут передаваться фикстуры;
    # Параметр expected_status - ожидаемый статус ответа.
    'parametrized_client, expected_status',
    # Предварительно оборачиваем имена фикстур
    # в вызов функции pytest.lazy_fixture().
    # В кортеже с кортежами передаём значения для параметров:
    (
        (pytest.lazy_fixture('admin_client'), HTTPStatus.NOT_FOUND),
        (pytest.lazy_fixture('author_client'), HTTPStatus.OK)
    ),
)
# Параметризуем тестирующую функцию:
@pytest.mark.parametrize(
    'name, args',
    (
        ('notes:detail', pytest.lazy_fixture('slug_for_args')),
        ('notes:edit', pytest.lazy_fixture('slug_for_args')),
        ('notes:delete', pytest.lazy_fixture('slug_for_args')),
    ),
)
# В параметры теста добавляем имена parametrized_client и expected_status.
def test_pages_availability_for_different_users(
        parametrized_client, name, args, expected_status
):
    """Проверка доступа пользователям до страницы отдельной заметки,
    её редактирования и удаления.
    """
    url = reverse(name, args=args)
    # Делаем запрос от имени клиента parametrized_client:
    response = parametrized_client.get(url)
    # Ожидаем ответ страницы, указанный в expected_status:
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    # Вторым параметром передаём note_object,
    # в котором будет либо фикстура с объектом заметки, либо None.
    'name, args',
    (
        ('notes:detail', pytest.lazy_fixture('slug_for_args')),
        ('notes:edit', pytest.lazy_fixture('slug_for_args')),
        ('notes:delete', pytest.lazy_fixture('slug_for_args')),
        ('notes:add', None),
        ('notes:success', None),
        ('notes:list', None),
    ),
)
# Передаём в тест анонимный клиент, name проверяемых страниц и args:
def test_redirects(client, name, args):
    login_url = reverse('users:login')
    # Формируем URL в зависимости от того, передан ли объект заметки:
    url = reverse(name, args=args)
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    # Ожидаем, что со всех проверяемых страниц анонимный клиент
    # будет перенаправлен на страницу логина:
    assertRedirects(response, expected_url)
