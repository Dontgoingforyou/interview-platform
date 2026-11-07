"""
URL-маршруты REST API приложения employees (эталон: interviews/api/).
"""
from django.urls import path
from rest_framework.routers import DefaultRouter

from employees import api_views as legacy_employee_json_views

from .admin_api_views import AdminDeveloperCountAPIView, AdminKpiReportAPIView
from .board_api_views import EmployeeManagersListAPIView, ManagerBoardAPIView
from .weekly_status_api import InternWeeklyStatusViewSet

router = DefaultRouter()
router.register(r'employees/weekly-statuses', InternWeeklyStatusViewSet, basename='weekly-status')

urlpatterns = [
    path('employees/search-intern/', legacy_employee_json_views.SearchInternView.as_view(), name='employees_search_intern'),
    path('employees/update-status/', legacy_employee_json_views.UpdateInternStatusView.as_view(), name='employees_update_status'),
    path(
        'employees/update-week-interviews/',
        legacy_employee_json_views.UpdateWeekInterviewCountView.as_view(),
        name='employees_update_week_interviews',
    ),
    path(
        'employees/update-week-absence/',
        legacy_employee_json_views.UpdateWeekAbsenceStatusView.as_view(),
        name='employees_update_week_absence',
    ),
    path(
        'employees/set-manager-active/',
        legacy_employee_json_views.SetManagerActiveView.as_view(),
        name='employees_set_manager_active',
    ),
    path('employees/managers/', EmployeeManagersListAPIView.as_view(), name='employees-managers-list'),
    path(
        'employees/managers/<str:email>/board/',
        ManagerBoardAPIView.as_view(),
        name='employees-manager-board',
    ),
    path('employees/admin/kpi/', AdminKpiReportAPIView.as_view(), name='employees-admin-kpi'),
    path(
        'employees/admin/developers/',
        AdminDeveloperCountAPIView.as_view(),
        name='employees-admin-developers',
    ),
] + router.urls
