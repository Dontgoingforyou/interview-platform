"""Тесты sad_intern.drf_list_query."""
from datetime import date, timedelta

import pytest

from core.constants import SAD_INTERN_STATUS_ON_PROJECT
from directions.models import Direction
from interns.models import Intern
from sad_intern.drf_list_query import (
    GROUPS_PER_PAGE,
    ON_PROJECT_PAGE_SIZE,
    PER_GROUP_PAGINATE_BY,
    apply_list_filters,
    apply_ordering,
    apply_q_search,
    build_grouped_payload,
    build_on_project_page,
    get_unique_direction_groups,
    sad_intern_role_scoped_qs,
)
from sad_intern.models import SadIntern


@pytest.mark.django_db(databases=['default'])
class TestSadInternRoleScopedQs:
    def test_admin_sees_all(self, api_admin_user, sad_intern):
        qs = sad_intern_role_scoped_qs(api_admin_user)
        assert qs.filter(pk=sad_intern.pk).exists()

    def test_hr_sees_all(self, api_hr_user, sad_intern, sad_intern_other):
        qs = sad_intern_role_scoped_qs(api_hr_user)
        assert qs.filter(pk=sad_intern.pk).exists()
        assert qs.filter(pk=sad_intern_other.pk).exists()

    def test_outstaff_sees_all(self, api_outstaff_user, sad_intern, sad_intern_other):
        qs = sad_intern_role_scoped_qs(api_outstaff_user)
        assert qs.count() >= 2

    def test_manager_sees_own(self, api_manager_user, sad_intern, manager):
        sad_intern.manager_email = manager.email
        sad_intern.save(update_fields=['manager_email'])
        qs = sad_intern_role_scoped_qs(api_manager_user)
        assert qs.filter(pk=sad_intern.pk).exists()

    def test_manager_does_not_see_other_manager_record(
        self, api_manager_user, sad_intern_other,
    ):
        qs = sad_intern_role_scoped_qs(api_manager_user)
        assert not qs.filter(pk=sad_intern_other.pk).exists()

    def test_manager_without_email_none(self, api_manager_user):
        api_manager_user.email = None
        assert sad_intern_role_scoped_qs(api_manager_user).count() == 0


@pytest.mark.django_db(databases=['default'])
class TestApplyQSearch:
    def test_empty_query_returns_unchanged(self, sad_intern):
        qs, direction_ids = apply_q_search(SadIntern.objects.all(), None)
        assert direction_ids is None
        assert qs.count() >= 1

    def test_search_by_name(self, sad_intern, intern):
        qs, _ = apply_q_search(SadIntern.objects.all(), intern.full_name[:4])
        assert qs.filter(pk=sad_intern.pk).exists()

    def test_search_by_direction_name(self, sad_intern, direction):
        qs, direction_ids = apply_q_search(SadIntern.objects.all(), direction.name[:3])
        assert direction_ids is not None
        assert direction.id in direction_ids
        assert qs.filter(pk=sad_intern.pk).exists()


@pytest.mark.django_db(databases=['default'])
class TestApplyListFilters:
    def test_waiting_excludes_on_project(self, sad_intern, sad_intern_on_project):
        qs = apply_list_filters(SadIntern.objects.all(), {}, waiting=True)
        assert qs.filter(pk=sad_intern.pk).exists()
        assert not qs.filter(pk=sad_intern_on_project.pk).exists()

    def test_not_waiting_only_on_project(self, sad_intern, sad_intern_on_project):
        qs = apply_list_filters(SadIntern.objects.all(), {}, waiting=False)
        assert qs.filter(pk=sad_intern_on_project.pk).exists()
        assert not qs.filter(pk=sad_intern.pk).exists()

    def test_status_filter(self, sad_intern, sad_intern_other):
        qs = apply_list_filters(
            SadIntern.objects.all(),
            {'status': 'rejected'},
            waiting=True,
        )
        assert qs.filter(pk=sad_intern.pk).exists()
        assert not qs.filter(pk=sad_intern_other.pk).exists()

    def test_direction_filter(self, sad_intern, direction):
        qs = apply_list_filters(
            SadIntern.objects.all(),
            {'direction': str(direction.id)},
            waiting=True,
        )
        assert qs.filter(pk=sad_intern.pk).exists()

    def test_invalid_direction_ignored(self, sad_intern):
        qs = apply_list_filters(
            SadIntern.objects.all(),
            {'direction': 'bad'},
            waiting=True,
        )
        assert qs.filter(pk=sad_intern.pk).exists()

    def test_manager_email_filter_when_allowed(self, sad_intern, manager):
        qs = apply_list_filters(
            SadIntern.objects.all(),
            {'manager_email': manager.email},
            waiting=True,
            allow_manager_email_filter=True,
        )
        assert qs.filter(pk=sad_intern.pk).exists()

    def test_manager_filter_without_at_ignored(self, sad_intern):
        qs = apply_list_filters(
            SadIntern.objects.all(),
            {'manager': 'no-email-here'},
            waiting=True,
            allow_manager_email_filter=True,
        )
        assert qs.filter(pk=sad_intern.pk).exists()


@pytest.mark.django_db(databases=['default'])
class TestApplyOrdering:
    @pytest.mark.parametrize('order_by', [
        'id', 'full_name', 'date_joined', 'days_waiting', 'telegram', 'status', 'manager',
    ])
    def test_valid_order_fields(self, two_ordered_sad_interns, order_by):
        sad_longer, sad_shorter = two_ordered_sad_interns
        qs = apply_ordering(
            SadIntern.objects.filter(pk__in=[sad_longer.pk, sad_shorter.pk]),
            order_by,
            'desc',
        )
        pks = list(qs.values_list('pk', flat=True))
        assert pks == [sad_longer.pk, sad_shorter.pk] if order_by == 'days_waiting' else len(pks) == 2

    def test_invalid_order_by_defaults_to_days_waiting(self, sad_intern):
        qs = apply_ordering(SadIntern.objects.all(), 'invalid', 'asc')
        assert qs.query.order_by


@pytest.mark.django_db(databases=['default'])
class TestGetUniqueDirectionGroups:
    def test_returns_sorted_direction_pairs(self, db, direction):
        dir_b = Direction.objects.create(name='Beta Track')
        for idx, dir_obj, name in (
            (1, direction, 'Alpha'),
            (2, dir_b, 'Beta'),
        ):
            intern = Intern.objects.create(
                full_name=name,
                direction=dir_obj,
                date_of_receipt=date(2025, 1, 1),
                date_of_birth=date(2000, 1, 1),
                hiring_hr='HR1',
                responsible_hr='HR2',
                group=f'GR{idx}',
                type_of_training='internal',
            )
            SadIntern.objects.create(intern=intern, waiting_since=date(2025, 11, idx))

        groups = get_unique_direction_groups(
            SadIntern.objects.select_related('intern', 'intern__direction')
        )
        names = [name for _did, name in groups]
        assert names == sorted(names)
        assert {g[0] for g in groups} == {direction.id, dir_b.id}


@pytest.mark.django_db(databases=['default'])
class TestBuildGroupedPayload:
    def test_empty_qs_returns_empty_groups(self):
        payload = build_grouped_payload(SadIntern.objects.none(), {})
        assert payload['groups'] == []
        assert payload['has_more_directions'] is False
        assert payload['next_directions_offset'] is None
        assert payload['total_directions'] == 0

    def test_grouped_results_and_has_more_directions(self, db, direction):
        directions = [direction]
        for i in range(GROUPS_PER_PAGE):
            directions.append(Direction.objects.create(name=f'Extra Dir {i}'))
        interns_and_sad = []
        for idx, dir_obj in enumerate(directions):
            intern = Intern.objects.create(
                full_name=f'Студент {idx}',
                direction=dir_obj,
                date_of_receipt=date(2025, 1, 1),
                date_of_birth=date(2000, 1, 1),
                hiring_hr='HR1',
                responsible_hr='HR2',
                group=f'GR{idx}',
                type_of_training='internal',
                real_interview_date=date.today() - timedelta(days=5),
            )
            sad = SadIntern.objects.create(
                intern=intern,
                waiting_since=date(2025, 11, 1) + timedelta(days=idx),
                status='rejected',
            )
            interns_and_sad.append(sad)

        qs = SadIntern.objects.filter(
            pk__in=[s.pk for s in interns_and_sad]
        ).select_related('intern', 'intern__direction')
        qs = apply_list_filters(qs, {}, waiting=True)

        payload = build_grouped_payload(qs, {'directions_offset': 0})
        assert len(payload['groups']) == GROUPS_PER_PAGE
        assert payload['has_more_directions'] is True
        assert payload['next_directions_offset'] == GROUPS_PER_PAGE
        assert payload['total_directions'] == len(directions)

    def test_per_group_pagination_empty_page_uses_last_page(self, db, direction):
        interns = []
        for i in range(PER_GROUP_PAGINATE_BY + 2):
            intern = Intern.objects.create(
                full_name=f'Paginate {i}',
                direction=direction,
                date_of_receipt=date(2025, 1, 1),
                date_of_birth=date(2000, 1, 1),
                hiring_hr='HR1',
                responsible_hr='HR2',
                group=f'P{i}',
                type_of_training='internal',
                real_interview_date=date.today() - timedelta(days=5),
            )
            interns.append(intern)
            SadIntern.objects.create(
                intern=intern,
                waiting_since=date(2025, 11, 1),
                status='rejected',
            )

        qs = SadIntern.objects.filter(
            intern__direction_id=direction.id
        ).select_related('intern', 'intern__direction')
        qs = apply_list_filters(qs, {}, waiting=True)
        pag_key = f'page_{direction.id}'

        payload = build_grouped_payload(
            qs,
            {pag_key: 999},
            groups_per_page=1,
            per_group=PER_GROUP_PAGINATE_BY,
        )
        group = payload['groups'][0]
        assert group['page'] == group['total_pages']
        assert len(group['results']) <= PER_GROUP_PAGINATE_BY

    def test_per_group_invalid_page_number_falls_back_to_first(self, db, direction):
        intern = Intern.objects.create(
            full_name='Один',
            direction=direction,
            date_of_receipt=date(2025, 1, 1),
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal',
            real_interview_date=date.today() - timedelta(days=5),
        )
        SadIntern.objects.create(intern=intern, waiting_since=date(2025, 11, 1), status='rejected')
        qs = SadIntern.objects.filter(pk__in=SadIntern.objects.values_list('pk', flat=True))
        qs = apply_list_filters(qs, {}, waiting=True)
        pag_key = f'page_{direction.id}'
        payload = build_grouped_payload(qs, {pag_key: 'abc'}, groups_per_page=1, per_group=5)
        assert payload['groups'][0]['page'] == 1


@pytest.mark.django_db(databases=['default'])
class TestBuildOnProjectPage:
    def test_paginates_on_project_records(self, sad_intern_on_project):
        qs = apply_list_filters(
            SadIntern.objects.filter(pk=sad_intern_on_project.pk),
            {},
            waiting=False,
        )
        page_data = build_on_project_page(qs, {'on_project_page': 1})
        assert page_data['count'] == 1
        assert len(page_data['results']) == 1
        assert page_data['results'][0].pk == sad_intern_on_project.pk

    def test_empty_page_returns_last_page(self, db, direction):
        interns = []
        for i in range(ON_PROJECT_PAGE_SIZE + 1):
            intern = Intern.objects.create(
                full_name=f'On Project {i}',
                direction=direction,
                date_of_receipt=date(2025, 1, 1),
                date_of_birth=date(2000, 1, 1),
                hiring_hr='HR1',
                responsible_hr='HR2',
                group=f'OP{i}',
                type_of_training='internal',
            )
            interns.append(intern)
            SadIntern.objects.create(
                intern=intern,
                waiting_since=date(2025, 10, 1),
                status=SAD_INTERN_STATUS_ON_PROJECT,
            )
        qs = SadIntern.objects.filter(status=SAD_INTERN_STATUS_ON_PROJECT)
        page_data = build_on_project_page(qs, {'on_project_page': 99})
        assert page_data['page'] == page_data['total_pages']

    def test_invalid_page_number_falls_back_to_first(self, sad_intern_on_project):
        qs = apply_list_filters(
            SadIntern.objects.filter(pk=sad_intern_on_project.pk),
            {},
            waiting=False,
        )
        page_data = build_on_project_page(qs, {'on_project_page': 'x'})
        assert page_data['page'] == 1
