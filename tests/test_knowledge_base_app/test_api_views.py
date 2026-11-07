import pytest
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status

from accounts.permissions import IsManagerOrAdmin


@pytest.mark.django_db
class TestKnowledgeBaseAPIAuth:
    def test_sections_list_401_without_auth(self, api_client):
        url = reverse('kb_api_sections')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_sections_list_403_anon_user(self, api_client, api_anon_user):
        api_client.force_authenticate(user=api_anon_user)
        url = reverse('kb_api_sections')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize('url_name,url_kwargs,http_method', [
        ('kb_api_search', {}, 'get'),
        ('kb_api_sections', {}, 'get'),
        ('kb_api_section_detail', {'section_id': 'any'}, 'get'),
        ('kb_api_articles', {'section_id': 'any'}, 'get'),
        ('kb_api_article_detail', {'section_id': 'any', 'filename': '01-x.md'}, 'get'),
    ])
    def test_anon_forbidden_on_all_read_endpoints(
        self, api_client, api_anon_user, url_name, url_kwargs, http_method,
    ):
        api_client.force_authenticate(user=api_anon_user)
        url = reverse(url_name, kwargs=url_kwargs)
        response = getattr(api_client, http_method)(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_not_authenticated_user_returns_401_when_permission_bypassed(
        self, api_client, api_manager_user,
    ):
        """_require_authenticated_user в initial() — 401 при is_authenticated=False."""
        api_manager_user.is_authenticated = False
        api_client.force_authenticate(user=api_manager_user)
        url = reverse('kb_api_sections')
        with patch.object(IsManagerOrAdmin, 'has_permission', return_value=True):
            response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestKnowledgeBaseAPISections:
    def test_sections_list_empty_manager(self, api_client, api_manager_user):
        api_client.force_authenticate(user=api_manager_user)
        url = reverse('kb_api_sections')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_sections_crud_admin(self, api_client, api_admin_user):
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('kb_api_sections')
        response = api_client.post(
            url,
            {'section_id': 'api-docs', 'title': 'API', 'description': 'd', 'icon': '📚'},
            format='json',
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['section_id'] == 'api-docs'

        list_resp = api_client.get(url)
        assert list_resp.status_code == status.HTTP_200_OK
        ids = [s['id'] for s in list_resp.json()]
        assert 'api-docs' in ids

        detail_url = reverse('kb_api_section_detail', kwargs={'section_id': 'api-docs'})
        patch_resp = api_client.patch(detail_url, {'title': 'API 2'}, format='json')
        assert patch_resp.status_code == status.HTTP_200_OK
        assert patch_resp.json()['title'] == 'API 2'

        del_resp = api_client.delete(detail_url)
        assert del_resp.status_code == status.HTTP_204_NO_CONTENT

    def test_create_section_403_manager(self, api_client, api_manager_user, kb_manager_with_section):
        api_client.force_authenticate(user=api_manager_user)
        url = reverse('kb_api_sections')
        response = api_client.post(
            url,
            {'section_id': 'x', 'title': 'X'},
            format='json',
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_section_400_missing_title(self, api_client, api_admin_user):
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('kb_api_sections')
        response = api_client.post(url, {'section_id': 'valid-id'}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_section_400_invalid_section_id(self, api_client, api_admin_user):
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('kb_api_sections')
        response = api_client.post(
            url,
            {'section_id': 'INVALID_ID', 'title': 'Заголовок'},
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'ID раздела' in str(response.data)

    def test_create_section_400_duplicate_section_id(
        self, api_client, api_admin_user, kb_manager_with_section,
    ):
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('kb_api_sections')
        response = api_client.post(
            url,
            {'section_id': 'test-section', 'title': 'Дубликат'},
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'уже существует' in str(response.data)

    def test_create_section_500_on_unexpected_error(self, api_client, api_admin_user):
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('kb_api_sections')
        with patch(
            'knowledge_base_app.api.views.KnowledgeBaseManager.create_section',
            side_effect=RuntimeError('disk'),
        ):
            response = api_client.post(
                url,
                {'section_id': 'new-sec', 'title': 'Новый'},
                format='json',
            )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()['detail'] == 'Не удалось создать раздел.'

    def test_section_detail_404(self, api_client, api_manager_user):
        api_client.force_authenticate(user=api_manager_user)
        url = reverse('kb_api_section_detail', kwargs={'section_id': 'missing-section'})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_section_patch_404(self, api_client, api_admin_user):
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('kb_api_section_detail', kwargs={'section_id': 'no-such'})
        response = api_client.patch(url, {'title': 'X'}, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_section_delete_404(self, api_client, api_admin_user):
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('kb_api_section_detail', kwargs={'section_id': 'ghost'})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestKnowledgeBaseAPIArticles:
    def test_articles_list_and_article_detail(self, api_client, api_manager_user, kb_manager_with_section):
        api_client.force_authenticate(user=api_manager_user)
        kb_manager_with_section.create_article('test-section', 'Статья 1', '# Текст')
        base = reverse('kb_api_articles', kwargs={'section_id': 'test-section'})
        r = api_client.get(base)
        assert r.status_code == status.HTTP_200_OK
        items = r.json()
        assert len(items) == 1
        filename = items[0]['filename']

        detail = reverse(
            'kb_api_article_detail',
            kwargs={'section_id': 'test-section', 'filename': filename},
        )
        dr = api_client.get(detail)
        assert dr.status_code == status.HTTP_200_OK
        body = dr.json()
        assert body['title'] == 'Статья 1'
        assert 'html' in body
        assert 'markdown' in body

    def test_article_mutations_admin_only(self, api_client, api_admin_user, api_manager_user, kb_manager_with_section):
        kb_manager_with_section.create_article('test-section', 'T', 'c')
        articles = kb_manager_with_section.get_articles('test-section')
        filename = articles[0]['filename']
        detail = reverse(
            'kb_api_article_detail',
            kwargs={'section_id': 'test-section', 'filename': filename},
        )

        api_client.force_authenticate(user=api_manager_user)
        assert api_client.patch(detail, {'title': 'H'}, format='json').status_code == status.HTTP_403_FORBIDDEN

        api_client.force_authenticate(user=api_admin_user)
        pr = api_client.patch(detail, {'title': 'Новый заголовок'}, format='json')
        assert pr.status_code == status.HTTP_200_OK
        assert pr.json()['title'] == 'Новый заголовок'

        create_url = reverse('kb_api_articles', kwargs={'section_id': 'test-section'})
        cr = api_client.post(create_url, {'title': 'Вторая'}, format='json')
        assert cr.status_code == status.HTTP_201_CREATED

    def test_create_article_403_manager(self, api_client, api_manager_user, kb_manager_with_section):
        api_client.force_authenticate(user=api_manager_user)
        url = reverse('kb_api_articles', kwargs={'section_id': 'test-section'})
        response = api_client.post(url, {'title': 'Новая'}, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_articles_list_404_unknown_section(self, api_client, api_manager_user):
        api_client.force_authenticate(user=api_manager_user)
        url = reverse('kb_api_articles', kwargs={'section_id': 'unknown-xyz'})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_article_404_unknown_section(self, api_client, api_admin_user):
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('kb_api_articles', kwargs={'section_id': 'no-section'})
        response = api_client.post(url, {'title': 'Статья'}, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_article_500_on_unexpected_error(
        self, api_client, api_admin_user, kb_manager_with_section,
    ):
        api_client.force_authenticate(user=api_admin_user)
        url = reverse('kb_api_articles', kwargs={'section_id': 'test-section'})
        with patch(
            'knowledge_base_app.api.views.KnowledgeBaseManager.create_article',
            side_effect=RuntimeError('io'),
        ):
            response = api_client.post(url, {'title': 'Ошибка'}, format='json')
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()['detail'] == 'Не удалось создать статью.'

    def test_article_detail_404(self, api_client, api_manager_user, kb_manager_with_section):
        api_client.force_authenticate(user=api_manager_user)
        url = reverse(
            'kb_api_article_detail',
            kwargs={'section_id': 'test-section', 'filename': '99-nonexistent.md'},
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_article_patch_400_without_fields(
        self, api_client, api_admin_user, kb_manager_with_section,
    ):
        kb_manager_with_section.create_article('test-section', 'T', 'body')
        filename = kb_manager_with_section.get_articles('test-section')[0]['filename']
        api_client.force_authenticate(user=api_admin_user)
        url = reverse(
            'kb_api_article_detail',
            kwargs={'section_id': 'test-section', 'filename': filename},
        )
        response = api_client.patch(url, {}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['detail'] == 'Укажите title и/или content.'

    def test_article_patch_content_only(
        self, api_client, api_admin_user, kb_manager_with_section,
    ):
        kb_manager_with_section.create_article('test-section', 'Заголовок', 'старое')
        filename = kb_manager_with_section.get_articles('test-section')[0]['filename']
        api_client.force_authenticate(user=api_admin_user)
        url = reverse(
            'kb_api_article_detail',
            kwargs={'section_id': 'test-section', 'filename': filename},
        )
        response = api_client.patch(url, {'content': '# Новый текст'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'Новый текст' in response.json()['markdown']

    def test_delete_article_403_manager(
        self, api_client, api_manager_user, api_admin_user, kb_manager_with_section,
    ):
        kb_manager_with_section.create_article('test-section', 'Del', 'x')
        filename = kb_manager_with_section.get_articles('test-section')[0]['filename']
        detail = reverse(
            'kb_api_article_detail',
            kwargs={'section_id': 'test-section', 'filename': filename},
        )
        api_client.force_authenticate(user=api_manager_user)
        assert api_client.delete(detail).status_code == status.HTTP_403_FORBIDDEN

    def test_delete_article_404_admin(self, api_client, api_admin_user, kb_manager_with_section):
        api_client.force_authenticate(user=api_admin_user)
        url = reverse(
            'kb_api_article_detail',
            kwargs={'section_id': 'test-section', 'filename': '88-missing.md'},
        )
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_article_204_admin(
        self, api_client, api_admin_user, kb_manager_with_section,
    ):
        kb_manager_with_section.create_article('test-section', 'Удалить', 'текст')
        filename = kb_manager_with_section.get_articles('test-section')[0]['filename']
        api_client.force_authenticate(user=api_admin_user)
        url = reverse(
            'kb_api_article_detail',
            kwargs={'section_id': 'test-section', 'filename': filename},
        )
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert kb_manager_with_section.get_article('test-section', filename) is None


@pytest.mark.django_db
class TestKnowledgeBaseAPISearch:
    def test_search_401_without_auth(self, api_client):
        url = reverse('kb_api_search')
        response = api_client.get(url, {'q': 'test'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_search_empty_query_returns_200(self, api_client, api_manager_user):
        api_client.force_authenticate(user=api_manager_user)
        url = reverse('kb_api_search')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)

    def test_search_no_results(self, api_client, api_manager_user, kb_manager_with_section):
        api_client.force_authenticate(user=api_manager_user)
        url = reverse('kb_api_search')
        response = api_client.get(url, {'q': 'zzz_kb_no_match_token_zzz'})
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_search(self, api_client, api_manager_user, kb_manager_with_section):
        token = 'kb_search_token_xyz'
        kb_manager_with_section.create_article('test-section', 'Статья для поиска', f'# {token}')
        api_client.force_authenticate(user=api_manager_user)
        url = reverse('kb_api_search')
        r = api_client.get(url, {'q': token.lower()})
        assert r.status_code == status.HTTP_200_OK
        data = r.json()
        assert len(data) == 1
        assert data[0]['title'] == 'Статья для поиска'

    def test_search_500_on_unexpected_error(self, api_client, api_manager_user):
        api_client.force_authenticate(user=api_manager_user)
        url = reverse('kb_api_search')
        with patch(
            'knowledge_base_app.api.views.KnowledgeBaseManager.search_articles',
            side_effect=RuntimeError('search failed'),
        ):
            response = api_client.get(url, {'q': 'x'})
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()['detail'] == 'Ошибка выполнения поиска.'
