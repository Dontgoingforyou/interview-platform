import type { ReactElement } from 'react'

export function HelpDebtsSection(): ReactElement {
  return (
    <>
      <p className="help-desc">Учёт финансовых договорённостей со студентами: займы, компенсации за обучение, обязательства перед платформой. Каждая запись — один договор с конкретной суммой, историей платежей и текущим статусом. Доступен только администраторам.</p>

      <h4 className="help-subtitle">Как считается баланс</h4>
      <div className="help-formula">
          <code>Остаток = Сумма договора − Уже заплатил</code>
      </div>
      <p className="help-desc">Остаток пересчитывается сам при каждом сохранении. Если остаток ноль или меньше — договор считается полностью закрытым.</p>

      <h4 className="help-subtitle">Поля записи о долге</h4>
      <div className="help-table-wrap">
          <table className="help-table">
              <thead><tr><th>Поле</th><th>Описание</th></tr></thead>
              <tbody>
                  <tr><td>Студент</td><td>Студент, с которым заключён договор.</td></tr>
                  <tr><td>Направление</td><td>Направление студента из справочника. Удобно для фильтров.</td></tr>
                  <tr><td>@tg</td><td>Telegram-ник студента. Используется в поиске.</td></tr>
                  <tr><td>Email</td><td>Электронная почта студента.</td></tr>
                  <tr><td>Сумма договора</td><td>Общая сумма обязательства по договору (в рублях).</td></tr>
                  <tr><td>Уже заплатил</td><td>Фактически внесённая сумма на текущий момент.</td></tr>
                  <tr><td>Остаток</td><td>Считается автоматически: сумма договора минус уже внесённые платежи.</td></tr>
                  <tr><td>Дата акта</td><td>Дата подписания договора (акта). Используется для сортировки и фильтрации.</td></tr>
                  <tr><td>Статус платежа</td><td>Текущее состояние выплат (см. ниже).</td></tr>
                  <tr><td>Комментарий</td><td>Произвольные заметки: условия договора, причина задолженности и т.д.</td></tr>
              </tbody>
          </table>
      </div>

      <h4 className="help-subtitle">Статусы платежа</h4>
      <div className="help-table-wrap">
          <table className="help-table">
              <thead><tr><th>Статус</th><th>Значение</th></tr></thead>
              <tbody>
                  <tr><td className="status-active">Платит</td><td>Студент выполняет обязательства — платежи поступают в срок или с небольшой задержкой.</td></tr>
                  <tr><td className="status-warning">Снова ищем</td><td>Студент прекратил платить или уволился с работы. Ведётся работа по возобновлению выплат или поиск новой работы.</td></tr>
                  <tr><td>Без статуса</td><td>Статус ещё не определён (новая запись) или не актуален.</td></tr>
              </tbody>
          </table>
      </div>

      <h4 className="help-subtitle">История платежей</h4>
      <p className="help-desc">К каждой записи долга прикреплена история платежей с разбивкой по месяцам и годам. В карточке отображаются последние 3 платежа. Все платежи доступны на странице редактирования записи. История позволяет отследить регулярность выплат.</p>

      <h4 className="help-subtitle">Подсветка строк</h4>
      <div className="help-table-wrap">
          <table className="help-table">
              <thead><tr><th>Цвет</th><th>Условие</th></tr></thead>
              <tbody>
                  <tr><td className="status-cancelled">Красный</td><td>Нет платежей за последние 4 месяца + остаток не равен нулю + дата акта старше 3 месяцев (не новичок).</td></tr>
                  <tr><td className="status-active">Зелёный</td><td>Остаток равен нулю — договор полностью закрыт.</td></tr>
              </tbody>
          </table>
      </div>

      <div className="help-note help-note--success">
          ⚡ При создании записи долга — статус студента в «Грустят» автоматически меняется на <strong>«Вышел на проект»</strong>. При удалении долга статус в «Грустят» <strong>не сбрасывается</strong>.
      </div>

      <h4 className="help-subtitle">Метрики</h4>
      <div className="metrics-grid">
          <div className="metric-card">
              <small>Всего людей</small>
              <strong>—</strong>
              <span className="muted">Количество записей в таблице долгов (если у одного студента несколько договоров — каждый считается отдельно)</span>
          </div>
          <div className="metric-card">
              <small>Активные должники</small>
              <strong>—</strong>
              <span className="muted">Договоры, по которым ещё есть ненулевой остаток к возврату</span>
          </div>
          <div className="metric-card">
              <small>Закрытые договоры</small>
              <strong>—</strong>
              <span className="muted">Записи с нулевым или отрицательным остатком — долг полностью погашен</span>
          </div>
          <div className="metric-card">
              <small>Общая сумма договоров</small>
              <strong>—</strong>
              <span className="muted">Сумма всех сумм договоров — общий объём обязательств</span>
          </div>
          <div className="metric-card">
              <small>Выплачено</small>
              <strong>—</strong>
              <span className="muted">Сколько всего уже внесено по всем договорам</span>
          </div>
          <div className="metric-card">
              <small>Остаток к получению</small>
              <strong>—</strong>
              <span className="muted">Сколько всего ещё осталось вернуть по всем договорам</span>
          </div>
          <div className="metric-card">
              <small>Средний остаток на активного</small>
              <strong>—</strong>
              <span className="muted">Остаток к получению / кол-во активных должников</span>
          </div>
          <div className="metric-card">
              <small>Средний прогресс выплат</small>
              <strong>—</strong>
              <span className="muted">Процент записей, у которых есть платежи за каждый из последних 3 месяцев (стабильно платят)</span>
          </div>
          <div className="metric-card">
              <small>Максимальный остаток</small>
              <strong>—</strong>
              <span className="muted">Самый крупный остаток по одному договору; под цифрой — у кого именно</span>
          </div>
          <div className="metric-card">
              <small>Людей без платежей</small>
              <strong>—</strong>
              <span className="muted">Записи, для которых нет ни одного платежа в истории платежей</span>
          </div>
      </div>

      <div className="help-note">
          🔑 Раздел «Долги» виден только <strong>администраторам</strong>.
      </div>
    </>
  )
}
