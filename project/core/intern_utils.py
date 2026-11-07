import logging
import re
from django.db.models import Q
from interns.models import Intern

logger = logging.getLogger(__name__)

# Разделители частей ФИО: пробелы и дефис (для имён вида «Анна-Мария»)
NAME_PARTS_RE = re.compile(r'[\s\-]+')
# Пунктуация в начале/конце части ФИО — убираем для сопоставления
NAME_PART_STRIP = '.,;:'

# Placeholder для «y» в середине слова: после translit заменяется на «ы» (Bytyk → Бытык).
# Только между согласными, чтобы не трогать Ilya → Илья (l-y-a).
CONSONANTS = 'bcdfghjklmnpqrstvwxzBCDFGHJKLMNPQRSTVWXZ'
MIDDLE_Y_PLACEHOLDER = '\u00A7'  # § (section sign), проходит через cyrtranslit без изменений
MIDDLE_Y_PATTERN_RE = re.compile(
    r'(?<=[' + CONSONANTS + r'])[yY](?=[' + CONSONANTS + r'])',
)

# Кириллические согласные + ь для правил по паттернам (не по словарю имён)
CYR_CONSONANTS = 'бвгджзйклмнпрстфхцчшщьБВГДЖЗЙКЛМНПРСТФХЦЧШЩЬ'
# В конце слова: не менее 2 букв + согласная+и (не перед й/я/а) → …+согласная+ий.
# Минимум 2 символа отсекает «ми»→«Мий»; «евгенти» даёт «евгентий» — правка в POST.
CYR_IIY_PATTERN_RE = re.compile(
    r'(.{2,})([' + CYR_CONSONANTS + r'])и(?!й|я|а)\b',
)
# В конце слова: -иа → -ия (Викториа→Виктория, Мариа→Мария, Анатолиа→Анатолия — все имена разом)
CYR_IA_TO_YA_RE = re.compile(r'(\w)иа\b')
# Григорьий → Григорий (артефакт после правила согласная+и→ий)
CYR_SOFT_IIY_RE = re.compile(r'ьий\b')

# Латинские варианты, которые cyrtranslit передаёт неверно.
PRE_TRANSLIT_REPLACEMENTS = [
    ('Sayd', 'Сайд'),
    ('Said', 'Сайд'),
    ('Ahmed', 'Ахмед'),
    ('Ahmet', 'Ахмед'),
]

# Точечные правки (только то, что не покрыто общими правилами по паттернам выше).
# Общие правила уже дают: -ий (из -и/ый), -ия (из -иа), x→кс, ё, ь в Игорь, -ей (Андрей, Сергей).
POST_TRANSLIT_FIXES = {
    'Алеxандер': 'Александр',
    'алеxандер': 'александр',
    'Алеxей': 'Алексей',
    'алеxей': 'алексей',
    'Андреи': 'Андрей',
    'андреи': 'андрей',
    'Артем': 'Артём',
    'артем': 'артём',
    'Ахмад': 'Ахмед',
    'ахмад': 'ахмед',
    'Дария': 'Дарья',
    'дария': 'дарья',
    'Даря': 'Дарья',
    'даря': 'дарья',
    'Евгенти': 'Евгений',
    'евгенти': 'евгений',
    'Евгентий': 'Евгений',
    'евгентий': 'евгений',
    'Жулиа': 'Юлия',
    'жулиа': 'юлия',
    'Игор': 'Игорь',
    'игор': 'игорь',
    'Иля': 'Илья',
    'иля': 'илья',
    'Маxим': 'Максим',
    'маxим': 'максим',
    'Сергеи': 'Сергей',
    'сергеи': 'сергей',
}


def _capitalize_name_parts(text):
    """Каждое слово (часть между пробелами/дефисами) с заглавной буквы."""
    parts = re.split(r'([\s\-]+)', text)
    return ''.join(
        p.capitalize() if p and not all(c in ' \t-' for c in p) else p
        for p in parts
    )


def transliterate_query_to_latin(cyrillic_query):
    """
    Транслитерирует поисковый запрос из кириллицы в латиницу (для поиска по БД).

    Используется в автодополнениях, где данные в БД хранятся в латинице,
    а пользователь вводит запрос на русском.
    Возвращает None, если строка не содержит кириллицы.
    """
    if not cyrillic_query:
        return None
    has_cyrillic = any('\u0400' <= ch <= '\u04FF' for ch in cyrillic_query)
    if not has_cyrillic:
        return None
    try:
        import cyrtranslit
        return cyrtranslit.to_latin(cyrillic_query.lower(), 'ru')
    except Exception as exc:
        logger.warning('Ошибка транслитерации запроса %r: %s', cyrillic_query, exc)
        return None


def transliterate_name_to_cyrillic(latin_name):
    """
    Транслитерирует ФИО из латиницы в кириллицу (библиотека cyrtranslit).

    Подставляются известные написания (Sayd/Said→Сайд, Ahmed/Ahmet→Ахмед), затем
    «y» в середине слова заменяется на placeholder (после translit → «ы»), строка
    в нижнем регистре передаётся в to_cyrillic, результат приводится к виду «Слово Слово»,
    placeholder заменяется на «ы», применяются POST_TRANSLIT_FIXES.
    """
    if not latin_name or not latin_name.replace(' ', '').replace('-', '').isascii():
        return latin_name
    work = latin_name
    for latin, cyrillic in PRE_TRANSLIT_REPLACEMENTS:
        work = re.sub(r'\b' + re.escape(latin) + r'\b', cyrillic, work, flags=re.IGNORECASE)
    # y в середине слова (не в конце) → ы: Bytyk → Бытык
    work = MIDDLE_Y_PATTERN_RE.sub(MIDDLE_Y_PLACEHOLDER, work)
    # Латиница: «shch» (как в паспортном транслите буквы щ) иначе даёт «ш»+«ч», а не «щ»
    work = re.sub(r'shch', 'shh', work, flags=re.IGNORECASE)
    try:
        import cyrtranslit
        work_lower = work.lower()
        result = cyrtranslit.to_cyrillic(work_lower, 'ru')
        result = result.replace(MIDDLE_Y_PLACEHOLDER, 'ы')
        result = _capitalize_name_parts(result)
        # cyrtranslit даёт -ый вместо -ий в конце слова перед пробелом (Dmitriy Ivanov → Дмитрый)
        result = re.sub(r'(\w)ый\b', r'\1ий', result)
        # Общие правила по паттернам (без словаря имён):
        # -иа в конце слова → -ия (Виктория, Мария, Анатолия, Валерия и т.д.)
        result = CYR_IA_TO_YA_RE.sub(r'\1ия', result)
        # не менее 2 букв + согласная+и в конце слова → …+согласная+ий (Дмитрий, Евгений, Валерий и т.д.)
        result = CYR_IIY_PATTERN_RE.sub(r'\1\2ий', result)
        # Григорьий → Григорий
        result = CYR_SOFT_IIY_RE.sub(r'ий', result)
        # Латинское "ts" в именах → "ц" (cyrtranslit даёт "тс")
        result = result.replace('Тс', 'Ц').replace('тс', 'ц')
        # Игор/игор — только как отдельное слово, иначе «Григори» превратится в «Григорьи»
        for wrong in ('Игор', 'игор'):
            right = POST_TRANSLIT_FIXES.get(wrong)
            if right:
                result = re.sub(r'\b' + re.escape(wrong) + r'\b', right, result)
        # Точечные правки (только то, что не покрыто общими правилами выше)
        for wrong, right in sorted(POST_TRANSLIT_FIXES.items(), key=lambda x: -len(x[0])):
            if wrong == right or wrong in ('Игор', 'игор'):
                continue
            if right.startswith(wrong) and len(right) > len(wrong):
                suffix = right[len(wrong):]
                lookahead = r'(?!й|я|а)' if suffix == 'й' else r'(?!' + re.escape(suffix) + r')'
                result = re.sub(re.escape(wrong) + lookahead, right, result)
            else:
                result = result.replace(wrong, right)
        # Фоллбэк: пустой или некорректный результат — показываем исходное имя
        if not result or not result.strip():
            return latin_name
        return result
    except Exception as exc:
        logger.warning('Ошибка транслитерации ФИО %r: %s', latin_name, exc)
        return latin_name


def _name_parts(full_name):
    """Разбивает ФИО на части по пробелам и дефисам (без пустых), убирает пунктуацию с краёв."""
    if not full_name:
        return []
    return [
        p.strip().strip(NAME_PART_STRIP)
        for p in NAME_PARTS_RE.split(full_name)
        if p.strip().strip(NAME_PART_STRIP)
    ]


def _find_intern_in_cache(full_name, interns_cache):
    """
    Ищет студента по ФИО в предзагруженном списке объектов Intern.

    Воспроизводит тот же алгоритм, что и find_intern_by_name с запросами к БД:
    1. Точное совпадение (без учёта регистра)
    2. Все части ФИО входят в full_name кандидата (аналог icontains по каждой части)
    3. При нескольких кандидатах — выбор по наибольшему количеству совпадающих частей
    4. Fallback по вхождению поисковой строки как подстроки (аналог icontains всей строки)
    """
    name_lower = full_name.strip().lower()
    name_parts = _name_parts(full_name)
    if not name_parts:
        return None

    # Шаг 1: точное совпадение (iexact)
    for intern in interns_cache:
        if intern.full_name.strip().lower() == name_lower:
            return intern

    # Шаг 2: все части входят в full_name кандидата (icontains по каждой части)
    candidates = [
        i for i in interns_cache
        if all(p.lower() in i.full_name.lower() for p in name_parts)
    ]

    if len(candidates) == 1:
        return candidates[0]
    elif len(candidates) > 1:
        best_match = None
        best_score = 0
        for intern in candidates:
            intern_parts = _name_parts(intern.full_name)
            score = len(set(name_parts) & set(intern_parts))
            if score > best_score:
                best_score = score
                best_match = intern
        if best_match:
            return best_match
        logger.warning(
            f"Найдено несколько студентов по ФИО '{full_name}', но не удалось выбрать лучший вариант.")
        return None

    # Шаг 3: fallback — вхождение всей строки как подстроки (icontains по полной строке)
    fallback = [i for i in interns_cache if name_lower in i.full_name.lower()]
    if len(fallback) == 1:
        return fallback[0]
    elif len(fallback) > 1:
        logger.warning(f"Найдено несколько студентов по ФИО '{full_name}' через подстроку.")
    else:
        logger.warning(f"Студент с ФИО '{full_name}' не найден.")
    return None


def find_intern_by_name(full_name, interns_cache=None):
    """
    Ищет студента по ФИО (даже если порядок слов отличается).

    Части ФИО выделяются по пробелам и дефисам, чтобы "Сайд-Ахмед" и "Сайд Ахмед"
    давали одинаковый набор частей и находили одну и ту же запись.

    Алгоритм поиска:
    1. Поиск по точному совпадению (без учета регистра)
    2. Поиск по совпадению всех частей в любом порядке
    3. Если найдено несколько - выбор по наибольшему количеству совпадающих частей
    4. Поиск по подстроке (fallback)

    Args:
        full_name: ФИО для поиска
        interns_cache: предзагруженный список объектов Intern. Если передан —
            поиск выполняется в памяти без запросов к БД (оптимизация N+1 при импорте).
            Если None — стандартный поиск через запросы к БД.
    """
    if not full_name:
        return None

    name_parts = _name_parts(full_name)
    if not name_parts:
        return None

    if interns_cache is not None:
        return _find_intern_in_cache(full_name, interns_cache)

    # Пытаемся найти по точному совпадению
    try:
        intern = Intern.objects.get(full_name__iexact=full_name.strip())
        return intern
    except Intern.DoesNotExist:
        pass  # Ищем дальше

    # Ищем по полному совпадению всех частей (пробел/дефис не мешают)
    query = Q()
    for part in name_parts:
        query &= Q(full_name__icontains=part)

    candidates = Intern.objects.filter(query)

    if candidates.count() == 1:
        return candidates.first()
    elif candidates.count() > 1:
        # Если несколько кандидатов — выбираем по наибольшему совпадению частей
        best_match = None
        best_score = 0
        for intern in candidates:
            intern_parts = _name_parts(intern.full_name)
            score = len(set(name_parts) & set(intern_parts))
            if score > best_score:
                best_score = score
                best_match = intern
        if best_match:
            return best_match
        else:
            logger.warning(
                f"Найдено несколько студентов по ФИО '{full_name}', но не удалось выбрать лучший вариант.")
            return None
    else:
        # Если не нашли — ищем по вхождению
        interns = Intern.objects.filter(full_name__icontains=full_name.strip())
        if interns.count() == 1:
            return interns.first()
        elif interns.count() > 1:
            logger.warning(f"Найдено несколько студентов по ФИО '{full_name}' через подстроку.")
            return None
        else:
            logger.warning(f"Студент с ФИО '{full_name}' не найден.")
            return None
