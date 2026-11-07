import type { ReactElement } from 'react'

export function HelpOffersSection(): ReactElement {
  return (
    <>
      <p className="help-desc">Раздел для фиксации успешных трудоустройств: кого из студентов взяли на работу, в какую компанию, на каком направлении и за какую сумму. Данные сгруппированы по месяцам и используются для отчётности и аналитики.</p>

      <h4 className="help-subtitle">Поля записи об оффере</h4>
      <div className="help-table-wrap">
          <table className="help-table">
              <thead><tr><th>Поле</th><th>Обязательное</th><th>Описание</th></tr></thead>
              <tbody>
                  <tr><td>Студент</td><td>Да</td><td>Студент, получивший оффер. Выбирается из списка студентов платформы.</td></tr>
                  <tr><td>Направление</td><td>Да</td><td>Техническое направление (Java, Python, Go, системный аналитик и др.) — выбирается из справочника направлений.</td></tr>
                  <tr><td>Компания</td><td>Да</td><td>Компания, выдавшая оффер. Название вводится вручную в форме.</td></tr>
                  <tr><td>Сумма</td><td>Нет</td><td>Сумма оффера в рублях. Используется во всех финансовых метриках раздела.</td></tr>
                  <tr><td>Месяц</td><td>Да</td><td>Месяц оффера — для группировки записей в списке и аналитики.</td></tr>
                  <tr><td>Год</td><td>Да</td><td>Год оффера. По умолчанию подставляется текущий год.</td></tr>
              </tbody>
          </table>
      </div>

      <h4 className="help-subtitle">Колонки таблицы</h4>
      <div className="help-table-wrap">
          <table className="help-table">
              <thead><tr><th>Колонка</th><th>Описание</th></tr></thead>
              <tbody>
                  <tr><td>ID</td><td>Номер записи в этом разделе.</td></tr>
                  <tr><td>ФИО</td><td>Имя студента, получившего оффер.</td></tr>
                  <tr><td>Направление</td><td>Техническое направление из справочника.</td></tr>
                  <tr><td>Компания</td><td>Название компании.</td></tr>
                  <tr><td>Сумма</td><td>Сумма оффера в рублях (целое число). Пусто, если не указана.</td></tr>
                  <tr><td>Телеграм</td><td>Telegram-аккаунт студента (берётся из карточки студента). Является ссылкой на профиль в Telegram.</td></tr>
                  <tr><td>Действия</td><td>Кнопка редактирования — для всех менеджеров. Кнопка удаления — только для администраторов.</td></tr>
              </tbody>
          </table>
      </div>

      <h4 className="help-subtitle">Группировка по месяцам</h4>
      <p className="help-desc">Записи сгруппированы по месяцам — «Январь 2025», «Февраль 2025» и т.д. Месяцы отображаются порциями по <strong>3 штуки</strong>, внутри каждого месяца — до <strong>10 записей</strong> на страницу. Кнопка «Загрузить следующие месяцы» подгружает следующую порцию без перезагрузки страницы.</p>

      <h4 className="help-subtitle">Фильтры</h4>
      <div className="help-table-wrap">
          <table className="help-table">
              <thead><tr><th>Фильтр</th><th>Описание</th></tr></thead>
              <tbody>
                  <tr><td>Поиск</td><td>Текстовый поиск по ФИО студента или названию компании.</td></tr>
                  <tr><td>Направление</td><td>Фильтрация по конкретному направлению (Java, Python, Go и др.).</td></tr>
                  <tr><td>Год</td><td>Фильтрация по году оффера.</td></tr>
                  <tr><td>Месяц</td><td>Фильтрация по месяцу оффера.</td></tr>
              </tbody>
          </table>
      </div>

      <h4 className="help-subtitle">Метрики</h4>
      <p className="help-desc">Все метрики рассчитываются по <strong>всем записям</strong> в базе — фильтры таблицы на них не влияют. Финансовые метрики (средний, медианный, максимальный, минимальный) учитывают только записи с заполненным полем «Сумма».</p>
      <div className="metrics-grid">
          <div className="metric-card light">
              <small>Всего офферов</small>
              <strong>—</strong>
              <span className="muted">Общее количество записей об офферах за всё время.</span>
          </div>
          <div className="metric-card light">
              <small>Уникальных направлений</small>
              <strong>—</strong>
              <span className="muted">Сколько разных направлений представлено в офферах.</span>
          </div>
          <div className="metric-card light">
              <small>Компаний в списке</small>
              <strong>—</strong>
              <span className="muted">Количество уникальных компаний с непустым названием.</span>
          </div>
          <div className="metric-card light">
              <small>Средний оффер</small>
              <strong>—</strong>
              <span className="muted">Среднее арифметическое суммы по всем записям с заполненным полем «Сумма».</span>
          </div>
          <div className="metric-card light">
              <small>Медианный оффер</small>
              <strong>—</strong>
              <span className="muted">Медиана — устойчива к выбросам, не завышается одним крупным оффером.</span>
          </div>
          <div className="metric-card light">
              <small>Максимальный оффер</small>
              <strong>—</strong>
              <span className="muted">Наибольшая зафиксированная сумма оффера.</span>
          </div>
          <div className="metric-card light">
              <small>Минимальный оффер</small>
              <strong>—</strong>
              <span className="muted">Наименьшая зафиксированная сумма оффера.</span>
          </div>
          <div className="metric-card light">
              <small>Самая популярная компания</small>
              <strong>—</strong>
              <span className="muted">Компания с наибольшим числом записей об офферах.</span>
          </div>
          <div className="metric-card light">
              <small>Компания с высоким средним</small>
              <strong>—</strong>
              <span className="muted">Компания с наибольшим средним значением суммы оффера.</span>
          </div>
          <div className="metric-card light">
              <small>Лучший месяц по среднему</small>
              <strong>—</strong>
              <span className="muted">Месяц и год, в котором среднее значение суммы офферов было наибольшим.</span>
          </div>
      </div>

      <h4 className="help-subtitle">Импорт из файла</h4>
      <p className="help-desc">Доступен администраторам. Форматы <strong>CSV</strong> и <strong>XLSX</strong>. В таблице должны быть колонки с заголовками, которые понимает система (как в образце для импорта), например:</p>
      <ul className="help-list">
          <li><strong>ФИ</strong> или <strong>ФИО</strong> — студент, как в системе.</li>
          <li><strong>Направление</strong> — как в справочнике направлений.</li>
          <li><strong>Компания</strong> — название компании.</li>
          <li><strong>Сумма</strong> (или «Сумма в оффере») — размер оффера числом.</li>
      </ul>
      <p className="help-desc">Месяц и год для блока строк задаются отдельной строкой-заголовком с названием месяца (например, «ФЕВРАЛЬ»). Повтор одного и того же студента за тот же месяц и год не загружается дважды. Импорт идёт в фоне — ход показывается на странице.</p>

      <div className="help-note">
          💡 После создания оффера студент перестаёт показываться в основном списке <strong>«Грустят»</strong>, если у него нет собеседований за последние 60 дней. Статус в «Грустят» при этом сам не меняется — строка просто скрывается из общего списка.
      </div>

      <div className="help-note">
          🔑 Редактировать оффер могут все менеджеры. Удалять записи могут только <strong>администраторы</strong>.
      </div>
    </>
  )
}
