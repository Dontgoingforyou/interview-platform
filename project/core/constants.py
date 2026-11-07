from datetime import date

COMPANY_OPTIONS = {
    'Яндекс': ['Яндекс', 'Yandex', 'Yandex Cloud'],
    'Ozon': ['Ozon', 'OZON', 'Озон'],
    'Северная лаборатория': ['Северная лаборатория', 'Sever Lab'],
    'Пример Банк': ['Пример Банк', 'Example Bank'],
}
DIRECTION_MAPPING = {
    'Devops': 'DevOps',
    'SA': 'Системный аналитик',
    'СА': 'Системный аналитик',
    'CA': 'Системный аналитик',
    'Системный Аналитик': 'Системный аналитик',
    'iOS': 'IOS',
    'ios': 'IOS',
    'Node': 'Node.js',
    'Node is': 'Node.js',
    'Node.JS': 'Node.js',
    'Go': 'GO',
    'Golang': 'GO',
    'Golang-разработчик': 'GO',
    '1C': '1С',
    '1С аналитика': '1С',
    'C#': 'C++',
    'С++': 'C++',
    'Backend': 'Python',
    'Python Backend': 'Python',
    'Python-разработчик': 'Python',
    'python-разработчик': 'Python',
    'Data Analyst': 'Аналитик данных',
    'Data analyst': 'Аналитик данных',
    'DA': 'Аналитик данных',
    'АД': 'Аналитик данных',
    'Аналитик': 'Аналитик данных',
    'Аналитика': 'Аналитик данных',
    'Аналитик Данных': 'Аналитик данных',
    'БА': 'Бизнес аналитик',
    'Бизнес-аналитик': 'Бизнес аналитик',
    '.Net': '.NET',
    'РНР': 'PHP',
    'Android-разработчик': 'Android',
    'Android разработчик': 'Android',
    'android-разработчик': 'Android',
    'QA': 'QA Manual',
    'QA manual': 'QA Manual',
    'AQA-Python': 'QA Manual',
    'Project manager': 'PM',
    'Fullstack-аналитик': 'Fullstack-аналитик',
}

MANAGER_MAPPING = {
    "Анна": "anna",
    "Иван": "ivan",
    "Мария": "maria",
}

MANAGER_TC_MAPPING = {
    "@Анна Иванова": "anna",
    "@Иван Петров": "ivan",
    "@Мария Соколова": "maria",
}

# Маппинг username → email для локального входа
MANAGER_EMAIL_MAPPING = {
    "anna": "anna.ivanova@example.com",
    "ivan": "ivan.petrov@example.com",
    "maria": "maria.sokolova@example.com",
}

INTERVIEW_TYPE_MAPPING = {
    'Скрининг': 'screening',
    'Техническое собеседование': 'tech',
    'Тех собес': 'tech',
    'Тех этап': 'tech',
    'тех этап': 'tech',
    'Тех этап': 'tech',
    'Техническое': 'tech',
    'техническое': 'tech',
    'HR собеседование': 'hr',
    'Финальное собеседование': 'final',
    'Финал': 'final',
    'финал': 'final',
    'Финальное': 'final',
    'финальное': 'final',
    'МОК собеседование': 'mock',
    'МОК': 'mock',
    'MOK': 'mock',
    'Мок': 'mock',
    'Тестовое задание': 'test',
    'Тест': 'test',
    'тест': 'test',
}

TYPE_OF_TRAINING_MAPPING = {
    'во вне': 'external',
    'outstaff': 'outstaff',
    'outstaff,во вне': 'external_or_outstaff',
    'во вне,outstaff': 'external_or_outstaff',
}

# --- Статусы и типы студента (Intern) ---
INTERN_STATUS_ACTIVE = 'активный'
INTERN_STATUS_LEFT = 'ушел'
INTERN_STATUS_OFFER = 'оффер'
INTERN_VALID_STATUSES = (INTERN_STATUS_ACTIVE, INTERN_STATUS_LEFT, INTERN_STATUS_OFFER)
INTERN_INACTIVE_STATUSES = (INTERN_STATUS_LEFT, INTERN_STATUS_OFFER)

INTERN_TRAINING_INTERNAL = 'internal'
INTERN_TRAINING_OUTSTAFF = 'outstaff'
INTERN_TRAINING_EXTERNAL = 'external'
INTERN_TRAINING_EXTERNAL_OR_OUTSTAFF = 'external_or_outstaff'

INTERN_IMPORT_COLUMN_MAPPING = {
    'ФИО': 'full_name',
    'Направление': 'direction_name',
    'Менеджер ТС': 'manager_name',
    'Тип обучения': 'type_of_training_label',
    'Дата рождения': 'date_of_birth_str',
    'Дата подписи': 'date_of_receipt_str',
    'Телеграм': 'telegram_username',
    'Группа': 'group',
    'Нанимающий HR': 'hiring_hr',
    'Ответственный HR': 'responsible_hr',
    'CV': 'cv',
    'CV (ау)': 'cv_au',
    'Город': 'city',
    'Легенда + коммент': 'legend',
    'Свойства': 'hr_feedback',
    'Доп контакты': 'additional_contacts_str',
}

INTERVIEW_COLUMN_MAPPING = {
    'ФИО': 'full_name',
    'Направление': 'direction_name',
    'Тип собеса': 'interview_type_label',
    'Дата': 'date_str',
    'Время': 'time_str',
    'Компания': 'company_name',
    'Ссылка на запись': 'link',
    'Менеджер': 'manager_name',
    'Ссылка на вакансию': 'vacancy_link',
    'Ссылка на собеседование': 'interview_link',
    'HR': 'hr_name',
    'Ссылка на тг': 'hr_contacts',
}

OFFER_COLUMN_MAPPING = {
    'ФИ': 'full_name',
    'ФИО': 'full_name',
    'Направление': 'direction_name',
    'Компания': 'company_name',
    'сумма в оффере': 'amount',
    'Сумма в оффере': 'amount',
    'Сумма': 'amount',
}

# Названия месяцев с заглавной (отчёты, формы). Строчной вариант — knowledge_base_app.constants.RUSSIAN_MONTHS.
MONTH_NAMES = [
    'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
    'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
]
MONTH_CHOICES = [(i, name) for i, name in enumerate(MONTH_NAMES, start=1)]
MONTH_NAME_TO_NUMBER = {
    'ЯНВАРЬ': 1, 'ФЕВРАЛЬ': 2, 'МАРТ': 3, 'АПРЕЛЬ': 4, 'МАЙ': 5, 'ИЮНЬ': 6,
    'ИЮЛЬ': 7, 'АВГУСТ': 8, 'СЕНТЯБРЬ': 9, 'ОКТЯБРЬ': 10, 'НОЯБРЬ': 11, 'ДЕКАБРЬ': 12
}

SAD_INTERN_COLUMN_MAPPING = {
    'ФИ': 'full_name',
    'Как долго сидит': 'waiting_since',
    'ТГ': 'telegram_username',
    'Менеджер': 'manager_name',
    'Статус': 'status',
    'Примечание': 'note',
}

SAD_INTERN_STATUS_MAPPING = {
    'Отказ': 'rejected',
    'Взяли': 'accepted',
    'Предложили': 'offered',
    'Уволили': 'fired',
    'Вышел на проект': 'on_project',
}

# Коды статусов SadIntern (для использования в коде без магических строк)
SAD_INTERN_STATUS_REJECTED = 'rejected'
SAD_INTERN_STATUS_ACCEPTED = 'accepted'
SAD_INTERN_STATUS_OFFERED = 'offered'
SAD_INTERN_STATUS_FIRED = 'fired'
SAD_INTERN_STATUS_ON_PROJECT = 'on_project'

# Минимальная дата выхода на реальные собеседования для автосоздания/автообновления SadIntern (сигнал Intern)
SAD_INTERN_ELIGIBLE_MIN_REAL_INTERVIEW_DATE = date(2026, 1, 10)

# --- Ограничения на длину ---
MAX_NAME_LENGTH = 255
MAX_URL_LENGTH = 500
MAX_TELEGRAM_LENGTH = 100
MAX_GROUP_LENGTH = 20
MAX_LONG_URL_LENGTH = 999

# --- Демо-группы ролей ---
KEYCLOAK_GROUP_ADMIN = 'role_admin'
KEYCLOAK_GROUP_EMPLOYMENT = 'employment-managers'
KEYCLOAK_GROUP_CV = 'cv-managers'
KEYCLOAK_GROUP_EDUCATION = 'education'
KEYCLOAK_GROUP_STUDENTS = 'students'
KEYCLOAK_GROUP_HR = 'hrs'
KEYCLOAK_GROUP_OUTSTAFF = 'outstaff'
KEYCLOAK_GROUP_MENTORS = 'mentors'
KEYCLOAK_MANAGER_GROUPS = {KEYCLOAK_GROUP_EMPLOYMENT, KEYCLOAK_GROUP_CV, KEYCLOAK_GROUP_EDUCATION}
# Группы, при которых пользователь считается имеющим доступ к приложению
KEYCLOAK_APP_KNOWN_GROUPS = frozenset(
    {
        KEYCLOAK_GROUP_ADMIN,
        KEYCLOAK_GROUP_EMPLOYMENT,
        KEYCLOAK_GROUP_CV,
        KEYCLOAK_GROUP_EDUCATION,
        KEYCLOAK_GROUP_HR,
        KEYCLOAK_GROUP_OUTSTAFF,
        KEYCLOAK_GROUP_MENTORS,
        KEYCLOAK_GROUP_STUDENTS,
    }
)
KEYCLOAK_ROLE_ADMIN = 'admin'
KEYCLOAK_ROLE_HR = 'hr'
KEYCLOAK_ROLE_OUTSTAFF = 'outstaff'
KEYCLOAK_ROLE_MENTOR = 'mentor'
KEYCLOAK_ROLE_STUDENT = 'student'
KEYCLOAK_ROLE_NO_ACCESS = 'no_access'

# --- HR и outstaff: только просмотр и фильтрация в разрешённых разделах (см. middleware) ---
HR_OUTSTAFF_ALLOWED_URL_NAMES = frozenset({
    'interview_list',
    'interviews_database_list',
    'directions_list',
    'directions_analytics_api',
    'directions_observations_api',
    'sad_intern_list',
    'sad_intern_analytics_api',
    'developer_list',
    'export_developers_table',
    'export_developers_metrics',
    'export_developers_chart',
    'get_intern_data',
    'intern_autocomplete',
    'company_autocomplete',
    'direction_autocomplete',
    'manager_autocomplete',
    'interview_transcription_status',
    'interview_transcription_text',
    'interview_transcribe',
    # Веб: стажёры и компании (только просмотр списков; merge/edit/delete — не в whitelist)
    'intern_list',
    'company_list',
    # Менеджеры и сотрудники (просмотр; API списка менеджеров и поиск на странице сотрудников)
    'managers_list',
    'managers_analytics_api',
    'managers_observations_api',
    'employees_list',
    'employees_detail',
    'employees_search_intern',
    # DRF (имена роутера): справочники, интервью и стажёры на чтение
    'direction-list',
    'direction-detail',
    'company-list',
    'company-detail',
    'interview-list',
    'interview-detail',
    'interview-transcription-text',
    'interview-transcription-status',
    'interview-transcribe',
    'intern-list',
    'intern-detail',
    # React API:
    'api_interviews_database_list',
    'employees-managers-list',
    'employees-manager-board',
    'weekly-status-list',
    'weekly-status-detail',
    'sad-intern-list',
    'sad-intern-detail',
    'sad-intern-grouped',
    'sad-intern-on-project',
    'api_sad_intern_analytics',
    'api-developer-stats',
})
HR_OUTSTAFF_ALLOWED_PATH_PREFIXES = (
    '/accounts/',
    '/static/',
    '/media/',
    '/api/auth/',
    '/api/analytics/',
    '/api/observations/',
    '/api/vector/',
)

# HR/outstaff: запрещённые пути SPA (создание/merge и т.п.) — редирект как у старых Django-view
HR_OUTSTAFF_BLOCKED_SPA_PATH_PREFIXES = (
    '/companies/merge',
    '/interviews/new',
)

# React SPA: префиксы путей для HROutstaffRedirectMiddleware (HR/outstaff не редиректить с этих URL)
HR_ALLOWED_REACT_PATH_PREFIXES = (
    '/interviews',
    '/interviews-database',
    '/directions',
    '/sad-intern',
    '/developers',
    '/interns',
    '/companies',
    '/managers',
    '/employees',
    '/auth',
    '/login',
    '/no-access',
)

# --- Менторы: только «База собеседований» (read-only, см. MentorRedirectMiddleware) ---
MENTOR_ALLOWED_URL_NAMES = frozenset({
    'interviews_database_list',
    'api_interviews_database_list',
    'direction-list',
    'direction-detail',
    'company-list',
    'company-detail',
    'interview-transcription-status',
    'interview-transcription-text',
    'interview-transcribe',
    'interview_transcribe',
})
MENTOR_ALLOWED_PATH_PREFIXES = (
    '/accounts/',
    '/static/',
    '/media/',
    '/api/auth/',
)
MENTOR_ALLOWED_REACT_PATH_PREFIXES = (
    '/interviews-database',
    '/auth',
    '/login',
    '/no-access',
)

# --- Типы собеседований ---
INTERVIEW_TYPE_SCREENING = 'screening'
INTERVIEW_TYPE_TECH = 'tech'
INTERVIEW_TYPE_HR = 'hr'
INTERVIEW_TYPE_FINAL = 'final'
INTERVIEW_TYPE_MOCK = 'mock'
INTERVIEW_TYPE_TEST = 'test'
INTERVIEW_TYPE_TECH_QUESTIONNAIRE = 'tech_questionnaire'
INTERVIEW_TYPE_CANCELLED = 'cancelled'

# --- Формат собеседования (онлайн / офис / телефон) ---
INTERVIEW_FORMAT_ONLINE = 'online'
INTERVIEW_FORMAT_OFFICE = 'office'
INTERVIEW_FORMAT_PHONE = 'phone'

INTERVIEW_FORMAT_CHOICES = (
    (INTERVIEW_FORMAT_ONLINE, 'Онлайн'),
    (INTERVIEW_FORMAT_OFFICE, 'Офис'),
    (INTERVIEW_FORMAT_PHONE, 'Телефонный звонок'),
)

# --- Статусы Debt ---
DEBT_PAYMENT_STATUS_SEARCHING = 'searching'
DEBT_PAYMENT_STATUS_PAYING = 'paying'
DEBT_PAYMENT_STATUS_UNKNOWN = 'unknown'
