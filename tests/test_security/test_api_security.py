"""
Security-тесты: IDOR и изоляция ролей.
"""
import pytest

from interns.models import Intern


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestInternManualStatusSecurity:
    def test_manual_status_forbidden_for_foreign_manager(
        self, api_client, api_manager_user, intern, direction, db,
    ):
        other = Intern.objects.create(
            full_name='Чужой',
            email='other@example.com',
            manager_email='other@example.com',
            direction=direction,
            date_of_receipt=__import__('datetime').date(2025, 1, 1),
            date_of_birth=__import__('datetime').date(2000, 1, 1),
            hiring_hr='HR',
            responsible_hr='HR',
            group='G',
            type_of_training='internal',
        )
        api_client.force_authenticate(user=api_manager_user)
        response = api_client.patch(
            f'/api/interns/{other.id}/manual-status/',
            {'manual_status': 'активный'},
            format='json',
        )
        assert response.status_code in (403, 404)


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestStudentApiIsolation:
    def test_student_forbidden_on_interviews_list(self, api_client, api_student_user):
        api_client.force_authenticate(user=api_student_user)
        response = api_client.get('/api/interviews/')
        assert response.status_code == 403

    def test_student_can_access_portal_interviews(self, api_client, api_student_user, intern, db):
        intern.corporate_email = api_student_user.email
        intern.save(update_fields=['corporate_email'])
        api_client.force_authenticate(user=api_student_user)
        response = api_client.get('/api/interns-portal/interviews/')
        assert response.status_code == 200


@pytest.mark.django_db(databases=['default'])
@pytest.mark.api
class TestHROutstaffWriteBlocked:
    def test_sad_intern_create_forbidden_for_hr(self, api_client, api_hr_user, direction):
        api_client.force_authenticate(user=api_hr_user)
        response = api_client.post(
            '/api/sad-interns/',
            {
                'intern': 1,
                'status': 'ожидание',
            },
            format='json',
        )
        assert response.status_code == 403
