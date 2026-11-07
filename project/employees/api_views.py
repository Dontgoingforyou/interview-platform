import logging
from datetime import datetime

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views import View
from django.http import Http404, JsonResponse

from interns.models import Intern
from managers.models import Manager
from employees.models import InternWeeklyStatus
from core.mixins import ManagerRequiredAPIView

logger = logging.getLogger(__name__)


class SearchInternView(ManagerRequiredAPIView, View):
    """API endpoint для поиска интерна по имени."""

    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '').strip()

        if not query:
            return JsonResponse({'error': 'Поисковый запрос не указан'}, status=400)

        # Ищем интернов по имени
        interns = Intern.objects.filter(full_name__icontains=query).only(
            'id', 'full_name', 'group', 'manager_email'
        )[:10]

        results = []
        for intern in interns:
            # Получаем email менеджера
            manager_email = intern.manager_email
            if not manager_email:
                continue

            results.append({
                'id': intern.id,
                'full_name': intern.full_name,
                'group': intern.group,
                'manager_email': manager_email,
            })

        return JsonResponse({
            'results': results,
            'count': len(results)
        })


class UpdateInternStatusView(ManagerRequiredAPIView, View):
    """API endpoint для обновления статуса интерна."""

    def post(self, request, *args, **kwargs):
        intern_id = request.POST.get('intern_id')
        new_status = request.POST.get('status')

        if not intern_id or not new_status:
            return JsonResponse({'error': 'Не указан ID интерна или новый статус'}, status=400)

        # Проверяем, что статус валидный
        from core.constants import INTERN_VALID_STATUSES
        if new_status not in INTERN_VALID_STATUSES:
            return JsonResponse({
                'error': f'Недопустимый статус. Допустимые значения: {", ".join(INTERN_VALID_STATUSES)}'
            }, status=400)

        try:
            intern = get_object_or_404(Intern, id=intern_id)
            intern.manual_status = new_status
            intern.save()
            logger.info(
                '[ОБНОВЛЕНИЕ] Пользователь %s обновил Intern id=%s: manual_status=%s',
                request.session.get('manager_name', 'неизвестно'),
                intern.id,
                new_status,
            )
            return JsonResponse({
                'success': True,
                'status': new_status,
                'status_display': intern.status_display
            })
        except Http404:
            return JsonResponse({'error': 'Интерн не найден'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class UpdateWeekInterviewCountView(ManagerRequiredAPIView, View):
    """API endpoint для обновления количества собеседований за неделю. Только для админов."""

    def post(self, request, *args, **kwargs):
        # Проверяем, что пользователь - админ
        if request.session.get('manager_role') != 'admin':
            logger.warning('Попытка редактирования недели не-админом: %s', request.session.get('manager_name'))
            return JsonResponse({'error': 'Редактирование доступно только администраторам'}, status=403)

        intern_id = request.POST.get('intern_id')
        week_start = request.POST.get('week_start')
        count = request.POST.get('count')
        user_name = request.session.get('manager_name', 'неизвестно')

        if not intern_id or not week_start:
            logger.error('Отсутствуют обязательные параметры')
            return JsonResponse({'error': 'Не указан ID интерна или дата начала недели'}, status=400)

        try:
            intern = get_object_or_404(Intern, id=intern_id)
            logger.info(f'Найден интерн: {intern.full_name}')

            # Парсим дату начала недели
            week_start_date = datetime.strptime(week_start, '%Y-%m-%d').date()
            logger.info(f'Дата недели распознана: {week_start_date}')

            # Обрабатываем значение count
            if count == '' or count is None:
                # Пустое значение - удаляем ручную корректировку
                manual_count = None
            else:
                try:
                    manual_count = int(count)
                    if manual_count < 0:
                        return JsonResponse({'error': 'Количество не может быть отрицательным'}, status=400)
                except ValueError:
                    return JsonResponse({'error': 'Некорректное значение количества'}, status=400)

            # Получаем или создаем запись недельного статуса
            weekly_status, created = InternWeeklyStatus.objects.get_or_create(
                intern=intern,
                week_start=week_start_date,
                defaults={'manual_interview_count': manual_count}
            )

            if created:
                logger.info(
                    '[СОЗДАНИЕ] Пользователь %s создал InternWeeklyStatus id=%s (intern_id=%s, week_start=%s)',
                    user_name, weekly_status.id, intern.id, week_start_date,
                )
            else:
                weekly_status.manual_interview_count = manual_count
                weekly_status.save()
                logger.info(
                    '[ОБНОВЛЕНИЕ] Пользователь %s обновил InternWeeklyStatus id=%s: manual_interview_count=%s',
                    user_name, weekly_status.id, manual_count,
                )

            # Если manual_count=None и absence_status=None, удаляем запись
            if weekly_status.manual_interview_count is None and not weekly_status.absence_status:
                deleted_id = weekly_status.id
                weekly_status.delete()
                logger.info(
                    '[УДАЛЕНИЕ] Пользователь %s удалил InternWeeklyStatus id=%s',
                    user_name, deleted_id,
                )
            return JsonResponse({
                'success': True,
                'count': manual_count
            })

        except Http404:
            logger.error('Интерн с ID %s не найден', intern_id)
            return JsonResponse({'error': 'Интерн не найден'}, status=404)
        except ValueError as e:
            logger.error(f'Ошибка парсинга даты: {e}')
            return JsonResponse({'error': f'Некорректный формат даты: {str(e)}'}, status=400)
        except Exception as e:
            logger.error(f'Неожиданная ошибка: {e}', exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)


class SetManagerActiveView(ManagerRequiredAPIView, View):
    """API endpoint для скрытия/восстановления менеджера. Только для администраторов."""

    def post(self, request, *args, **kwargs):
        if request.session.get('manager_role') != 'admin':
            return JsonResponse({'error': 'Доступно только администраторам'}, status=403)

        manager_email = request.POST.get('manager_email')
        is_active = request.POST.get('is_active', 'false').lower() == 'true'

        if not manager_email:
            return JsonResponse({'error': 'Не указан email менеджера'}, status=400)

        try:
            manager = Manager.objects.get(email=manager_email)
            manager.is_active = is_active
            manager.hidden_at = None if is_active else timezone.now()
            manager.save(update_fields=['is_active', 'hidden_at'])
            logger.info(
                '[ОБНОВЛЕНИЕ] Пользователь %s обновил Manager %s: is_active=%s',
                request.session.get('manager_name', 'неизвестно'),
                manager.full_name,
                is_active,
            )
            return JsonResponse({
                'success': True,
                'email': manager_email,
                'is_active': is_active,
                'full_name': manager.full_name,
            })
        except Manager.DoesNotExist:
            return JsonResponse({'error': 'Менеджер не найден'}, status=404)
        except Exception as e:
            logger.exception('Ошибка при изменении статуса менеджера')
            return JsonResponse({'error': str(e)}, status=500)


class UpdateWeekAbsenceStatusView(ManagerRequiredAPIView, View):
    """API endpoint для установки статуса отсутствия на неделю. Доступно для менеджеров и админов."""

    def post(self, request, *args, **kwargs):
        intern_id = request.POST.get('intern_id')
        week_start = request.POST.get('week_start')
        absence_status = request.POST.get('absence_status')
        absence_notes = request.POST.get('absence_notes', '')

        if not intern_id or not week_start:
            logger.error('Отсутствуют обязательные параметры')
            return JsonResponse({'error': 'Не указан ID интерна или дата начала недели'}, status=400)

        try:
            intern = get_object_or_404(Intern, id=intern_id)

            # Парсим дату начала недели
            week_start_date = datetime.strptime(week_start, '%Y-%m-%d').date()
            user_name = request.session.get('manager_name', 'неизвестно')

            # Проверяем валидность статуса
            valid_statuses = list(InternWeeklyStatus.ABSENCE_STATUS_VALUES) + ['']
            if absence_status and absence_status not in valid_statuses:
                logger.error(f'Недопустимый статус: {absence_status}')
                return JsonResponse({'error': 'Недопустимый статус отсутствия'}, status=400)

            # Если статус пустой - это удаление статуса отсутствия
            if not absence_status or absence_status == '':
                try:
                    weekly_status = InternWeeklyStatus.objects.get(
                        intern=intern,
                        week_start=week_start_date
                    )
                    weekly_status.absence_status = None
                    weekly_status.absence_notes = ''

                    if weekly_status.manual_interview_count is None:
                        deleted_id = weekly_status.id
                        weekly_status.delete()
                        logger.info(
                            '[УДАЛЕНИЕ] Пользователь %s удалил InternWeeklyStatus id=%s',
                            user_name, deleted_id,
                        )
                    else:
                        weekly_status.save()
                        logger.info(
                            '[ОБНОВЛЕНИЕ] Пользователь %s обновил InternWeeklyStatus id=%s: absence_status сброшен',
                            user_name, weekly_status.id,
                        )
                except InternWeeklyStatus.DoesNotExist:
                    pass

                return JsonResponse({
                    'success': True,
                    'absence_status': None,
                    'absence_status_display': None
                })

            # Получаем или создаем запись недельного статуса
            weekly_status, created = InternWeeklyStatus.objects.get_or_create(
                intern=intern,
                week_start=week_start_date,
                defaults={
                    'absence_status': absence_status,
                    'absence_notes': absence_notes
                }
            )

            if created:
                logger.info(
                    '[СОЗДАНИЕ] Пользователь %s создал InternWeeklyStatus id=%s (intern_id=%s, week_start=%s, absence_status=%s)',
                    user_name, weekly_status.id, intern.id, week_start_date, absence_status,
                )
            else:
                weekly_status.absence_status = absence_status
                weekly_status.absence_notes = absence_notes
                weekly_status.save()
                logger.info(
                    '[ОБНОВЛЕНИЕ] Пользователь %s обновил InternWeeklyStatus id=%s: absence_status=%s',
                    user_name, weekly_status.id, absence_status,
                )

            return JsonResponse({
                'success': True,
                'absence_status': absence_status,
                'absence_status_display': weekly_status.get_absence_status_display()
            })

        except Http404:
            logger.error('Интерн с ID %s не найден', intern_id)
            return JsonResponse({'error': 'Интерн не найден'}, status=404)
        except ValueError as e:
            logger.error('Ошибка парсинга даты: %s', e)
            return JsonResponse({'error': f'Некорректный формат даты: {str(e)}'}, status=400)
        except Exception as e:
            logger.error('Неожиданная ошибка: %s', e, exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)
