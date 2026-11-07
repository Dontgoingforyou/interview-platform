import pytest
from django.core.management import call_command

from companies.models import Company
from debts.models import Debt, PaymentHistory
from employees.models import InternWeeklyStatus
from interns.models import Intern
from interviews.models import Interview
from knowledge_base_app.models import KBArticle
from offers.models import Offer
from sad_intern.models import SadIntern
from transcriptions.models import InterviewTranscription, TranscriptionStatus


@pytest.mark.django_db(databases=['default'])
def test_seed_demo_data_is_idempotent():
    call_command('seed_demo_data')
    call_command('seed_demo_data')

    student = Intern.objects.get(email='student@example.com')
    assert Intern.objects.filter(email='maria.sokolova@example.com').count() == 1
    assert Company.objects.filter(name='Пример Банк').count() == 1
    assert Interview.objects.filter(intern=student).count() == 2
    assert Interview.objects.filter(link='https://example.com/demo-call').count() == 1
    assert InterviewTranscription.objects.filter(status=TranscriptionStatus.COMPLETED).count() == 1
    assert Offer.objects.count() == 2
    assert Debt.objects.count() == 1
    assert PaymentHistory.objects.count() == 2
    assert InternWeeklyStatus.objects.filter(intern=student).count() == 1
    assert KBArticle.objects.filter(filename='start').count() == 1
    assert SadIntern.objects.filter(intern=student).count() == 1
    assert SadIntern.objects.filter(intern__email='maria.sokolova@example.com', status='on_project').count() == 1
