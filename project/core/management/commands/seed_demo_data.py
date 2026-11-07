"""Демо-записи для локального просмотра портала. Повторный запуск не создаёт дубли."""
from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.demo_users import DEMO_USERS
from companies.models import Company
from core.constants import (
    DEBT_PAYMENT_STATUS_PAYING,
    INTERN_TRAINING_INTERNAL,
    INTERVIEW_TYPE_SCREENING,
    INTERVIEW_TYPE_TECH,
)
from core.constants import SAD_INTERN_STATUS_ON_PROJECT
from debts.models import Debt, PaymentHistory
from directions.models import Direction
from employees.models import InternWeeklyStatus
from interns.models import Intern
from interviews.models import Interview
from knowledge_base_app.models import KBArticle, KBSection
from managers.models import Manager
from offers.models import Offer
from sad_intern.models import SadIntern
from transcriptions.models import InterviewTranscription, TranscriptionStatus

MANAGER_EMAIL = 'ivan.petrov@example.com'
STUDENT_EMAIL = 'student@example.com'
SECOND_STUDENT_EMAIL = 'maria.sokolova@example.com'


class Command(BaseCommand):
    help = (
        'Учебные записи для разделов портала: студенты, собеседования, офферы, долги, '
        'грустят, недельный статус, база собеседований и база знаний'
    )

    @transaction.atomic
    def handle(self, *args, **options):
        for account in DEMO_USERS:
            if 'students' in account['groups']:
                continue
            Manager.objects.update_or_create(
                email=account['email'],
                defaults={
                    'full_name': account['full_name'],
                    'username': account['username'],
                    'groups': list(account['groups']),
                    'is_active': True,
                },
            )

        python = Direction.objects.get_or_create(name='Python')[0]
        frontend = Direction.objects.get_or_create(name='Frontend')[0]
        bank = Company.objects.get_or_create(name='Пример Банк', defaults={'is_bigtech': False})[0]
        Company.objects.get_or_create(name='Северная лаборатория', defaults={'is_bigtech': False})

        student, _ = Intern.objects.get_or_create(
            email=STUDENT_EMAIL,
            defaults={
                'full_name': 'Студент Демонов',
                'corporate_email': STUDENT_EMAIL,
                'telegram_username': 'demo_student',
                'direction': python,
                'city': 'Москва',
                'hiring_hr': 'Демо HR',
                'responsible_hr': 'Демо HR',
                'group': 'demo-python',
                'type_of_training': INTERN_TRAINING_INTERNAL,
                'manager_email': MANAGER_EMAIL,
                'real_interview_date': date(2026, 10, 1),
            },
        )
        second, _ = Intern.objects.get_or_create(
            email=SECOND_STUDENT_EMAIL,
            defaults={
                'full_name': 'Мария Соколова',
                'corporate_email': SECOND_STUDENT_EMAIL,
                'direction': frontend,
                'city': 'Казань',
                'hiring_hr': 'Демо HR',
                'responsible_hr': 'Демо HR',
                'group': 'demo-frontend',
                'type_of_training': INTERN_TRAINING_INTERNAL,
                'manager_email': MANAGER_EMAIL,
            },
        )

        Interview.objects.get_or_create(
            intern=student,
            company=bank,
            interview_type=INTERVIEW_TYPE_SCREENING,
            date=date(2026, 11, 3),
            defaults={
                'direction': python,
                'manager_email': MANAGER_EMAIL,
                'hr_name': 'Ольга Демо',
            },
        )
        tech, _ = Interview.objects.get_or_create(
            intern=student,
            company=bank,
            interview_type=INTERVIEW_TYPE_TECH,
            date=date(2026, 11, 12),
            defaults={
                'direction': python,
                'manager_email': MANAGER_EMAIL,
                'link': 'https://example.com/demo-call',
            },
        )
        if not tech.link:
            tech.link = 'https://example.com/demo-call'
            tech.save(update_fields=['link'])
        InterviewTranscription.objects.get_or_create(
            interview=tech,
            defaults={
                'status': TranscriptionStatus.COMPLETED,
                'text': 'Учебная расшифровка. Вопросы про Python и базы данных, без боевой записи.',
            },
        )
        Offer.objects.get_or_create(
            intern=second,
            month=10,
            year=2026,
            defaults={
                'direction': frontend,
                'company': 'Северная лаборатория',
                'amount': Decimal('160000.00'),
            },
        )
        Offer.objects.get_or_create(
            intern=second,
            month=11,
            year=2026,
            defaults={
                'direction': frontend,
                'company': 'Пример Банк',
                'amount': Decimal('180000.00'),
            },
        )
        debt, _ = Debt.objects.get_or_create(
            intern=second,
            defaults={
                'direction': frontend,
                'email': SECOND_STUDENT_EMAIL,
                'total_amount': Decimal('150000.00'),
                'paid_amount': Decimal('50000.00'),
                'payment_status': DEBT_PAYMENT_STATUS_PAYING,
                'act_date': date(2026, 9, 1),
            },
        )
        PaymentHistory.objects.get_or_create(
            debt=debt,
            month=9,
            year=2026,
            defaults={'amount': Decimal('25000.00')},
        )
        PaymentHistory.objects.get_or_create(
            debt=debt,
            month=10,
            year=2026,
            defaults={'amount': Decimal('25000.00')},
        )
        InternWeeklyStatus.objects.get_or_create(
            intern=student,
            week_start=date(2026, 11, 2),
            defaults={
                'absence_status': 'отпуск',
                'absence_notes': 'Учебная отметка на доске сотрудников',
            },
        )
        SadIntern.objects.filter(intern=student, note='').update(note='Ждёт обратную связь после скрининга')
        SadIntern.objects.filter(intern=student, note__isnull=True).update(
            note='Ждёт обратную связь после скрининга',
        )
        SadIntern.objects.get_or_create(
            intern=second,
            defaults={
                'waiting_since': date(2026, 8, 1),
                'telegram_username': 'demo_maria',
                'manager_email': MANAGER_EMAIL,
                'status': SAD_INTERN_STATUS_ON_PROJECT,
                'note': 'Учебная запись: вышла на проект',
            },
        )

        section, _ = KBSection.objects.get_or_create(
            section_id='demo',
            defaults={'title': 'Демо', 'description': 'Короткие заметки для локального портала', 'order': 1},
        )
        KBArticle.objects.get_or_create(
            section=section,
            filename='start',
            defaults={
                'title': 'С чего начать',
                'content': 'Это учебные записи. Боевых карточек студентов здесь нет.',
            },
        )

        self.stdout.write(self.style.SUCCESS(
            'Учебные записи на месте: студенты, собеседования, офферы, долг с платежами, '
            'грустят, недельный статус, транскрипция и статья базы знаний.'
        ))
