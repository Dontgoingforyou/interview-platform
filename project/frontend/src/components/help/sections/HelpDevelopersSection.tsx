import type { ReactElement } from 'react'

export function HelpDevelopersSection(): ReactElement {
  return (
    <>
      <p className="help-desc">Сводная статистика по студентам-разработчикам: объединяет данные из офферов и собеседований. Показывает активность каждого специалиста, количество пройденных интервью и динамику офферов по месяцам.</p>

      <h4 className="help-subtitle">Кто попадает в список</h4>
      <p className="help-desc">В таблицу включаются студенты, у которых выполнено хотя бы одно из условий:</p>
      <ul className="help-list">
          <li>Есть хотя бы одно собеседование, кроме помеченного как «НЕ СОСТОЯЛОСЬ».</li>
          <li>Есть хотя бы один оффер.</li>
      </ul>
      <p className="help-desc">Каждая строка — это пара «студент + направление». Если студент проходил собесы по нескольким направлениям или получал офферы в разных направлениях, он будет отображён несколькими строками.</p>

      <h4 className="help-subtitle">Колонки таблицы</h4>
      <div className="help-table-wrap">
          <table className="help-table">
              <thead><tr><th>Колонка</th><th>Описание</th></tr></thead>
              <tbody>
                  <tr><td>ФИО</td><td>Имя студента-разработчика.</td></tr>
                  <tr><td>Направление</td><td>Направление из справочника (Java, Python, Go и т.д.).</td></tr>
                  <tr><td>Последняя активность</td><td>Дата последнего собеседования, кроме «НЕ СОСТОЯЛОСЬ».</td></tr>
                  <tr><td>Кол-во интервью</td><td>Сколько таких собеседований по этому направлению всего (без отменённых).</td></tr>
              </tbody>
          </table>
      </div>

      <h4 className="help-subtitle">Фильтры</h4>
      <div className="help-table-wrap">
          <table className="help-table">
              <thead><tr><th>Фильтр</th><th>Описание</th></tr></thead>
              <tbody>
                  <tr><td>Направление</td><td>Фильтрация по конкретному направлению (Java, Python, Go и т.д.).</td></tr>
                  <tr><td>Поиск по ФИО</td><td>Текстовый поиск по имени разработчика.</td></tr>
              </tbody>
          </table>
      </div>

      <h4 className="help-subtitle">Метрики</h4>
      <p className="help-desc">Каждая метрика рассчитывается за своё фиксированное окно — не зависит от фильтров таблицы.</p>
      <div className="metrics-grid">
          <div className="metric-card">
              <small>Всего специалистов</small>
              <strong>—</strong>
              <span className="muted">Уникальных студентов с хотя бы одним не отменённым собеседованием за последние 15 дней</span>
          </div>
          <div className="metric-card">
              <small>Получили офферы</small>
              <strong>—</strong>
              <span className="muted">Уникальных пар «студент + направление» с оффером за текущий календарный год</span>
          </div>
          <div className="metric-card">
              <small>Средний оффер</small>
              <strong>—</strong>
              <span className="muted">Среднее значение суммы оффера по всем офферам за прошлый месяц</span>
          </div>
          <div className="metric-card">
              <small>Топ направление по скорости</small>
              <strong>—</strong>
              <span className="muted">Направление с минимальным средним кол-вом дней от первого до последнего собеседования среди получивших оффер за прошлый месяц. Под названием — среднее кол-во дней</span>
          </div>
          <div className="metric-card">
              <small>Топ направление по кол-ву офферов</small>
              <strong>—</strong>
              <span className="muted">Направление с наибольшим числом офферов за прошлый месяц</span>
          </div>
      </div>

      <h4 className="help-subtitle">График</h4>
      <p className="help-desc">Линейный график «Активность по месяцам» — показывает <strong>количество офферов</strong> за каждый из последних <strong>12 месяцев</strong>. Отображается ниже таблицы и не зависит от текущих фильтров.</p>

      <h4 className="help-subtitle">Экспорт в Excel</h4>
      <p className="help-desc">Доступны три отдельных файла:</p>
      <ul className="help-list">
          <li><strong>Скачать таблицу</strong> — ФИО, Направление, Последняя активность, Количество интервью по каждому разработчику с учётом текущих фильтров.</li>
          <li><strong>Скачать метрики</strong> — сводные цифры пяти метрик раздела (без фильтров).</li>
          <li><strong>Скачать график</strong> — исходные данные графика (месяц → кол-во офферов за последние 12 месяцев).</li>
      </ul>

      <div className="help-note">
          📥 Кнопки экспорта расположены над метриками и над таблицей. Файлы формируются мгновенно.
      </div>
    </>
  )
}
