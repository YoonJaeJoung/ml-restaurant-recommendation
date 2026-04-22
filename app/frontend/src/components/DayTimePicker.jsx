import { useEffect, useMemo, useState } from 'react'

const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

const MEAL_PRESETS = [
  { key: 'breakfast', label: 'Breakfast', hour:  9, minute: 0 },
  { key: 'lunch',     label: 'Lunch',     hour: 12, minute: 0 },
  { key: 'dinner',    label: 'Dinner',    hour: 18, minute: 0 },
]

function pad(n) { return String(n).padStart(2, '0') }
function toTimeStr(d) { return `${pad(d.getHours())}:${pad(d.getMinutes())}` }

function nextMatching(base, weekdayIdx) {
  const jsDayMon0 = (base.getDay() + 6) % 7
  let delta = weekdayIdx - jsDayMon0
  if (delta < 0) delta += 7
  const d = new Date(base)
  d.setDate(d.getDate() + delta)
  return d
}

function sameDay(a, b) {
  return a.getFullYear() === b.getFullYear()
      && a.getMonth() === b.getMonth()
      && a.getDate() === b.getDate()
}

function deriveDayMode(value) {
  if (!value) return 'today'
  const today = new Date()
  const tomorrow = new Date(); tomorrow.setDate(today.getDate() + 1)
  if (sameDay(value, today))    return 'today'
  if (sameDay(value, tomorrow)) return 'tomorrow'
  return 'select'
}

// Match the stored hour/minute to a meal preset or fall through to 'custom'.
function deriveTimeMode(value) {
  if (!value) return 'lunch'
  const h = value.getHours(), m = value.getMinutes()
  for (const p of MEAL_PRESETS) {
    if (h === p.hour && m === p.minute) return p.key
  }
  return 'custom'
}

export default function DayTimePicker({ value, onChange, anyTime, onAnyTime }) {
  const [dayMode, setDayMode]   = useState(() => deriveDayMode(value))
  const [timeMode, setTimeMode] = useState(() => deriveTimeMode(value))

  // Keep modes aligned when Clear resets the date from outside.
  useEffect(() => {
    const dd = deriveDayMode(value)
    if (dayMode !== 'select' || dd !== 'select') setDayMode(dd)
    setTimeMode(deriveTimeMode(value))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value?.getTime()])

  const timeStr = useMemo(() => toTimeStr(value || new Date()), [value])
  const selectedWeekday = useMemo(() => {
    if (!value) return null
    return (value.getDay() + 6) % 7
  }, [value])

  const applyWithTime = (d) => {
    if (value) { d.setHours(value.getHours()); d.setMinutes(value.getMinutes()) }
    onChange(d)
  }

  // ── Day selection ──────────────────────────────────────────────────
  const pickToday = () => {
    setDayMode('today'); onAnyTime?.(false)
    const d = new Date(); applyWithTime(d)
  }
  const pickTomorrow = () => {
    setDayMode('tomorrow'); onAnyTime?.(false)
    const d = new Date(); d.setDate(d.getDate() + 1); applyWithTime(d)
  }
  const pickSelectDay = () => {
    setDayMode('select'); onAnyTime?.(false)
    if (selectedWeekday == null) {
      const today = new Date()
      const idx = (today.getDay() + 6) % 7
      applyWithTime(nextMatching(today, idx))
    }
  }
  const pickWeekday = (idx) => applyWithTime(nextMatching(new Date(), idx))

  // ── Time selection ─────────────────────────────────────────────────
  const pickMeal = (p) => {
    setTimeMode(p.key); onAnyTime?.(false)
    const d = new Date(value || new Date())
    d.setHours(p.hour); d.setMinutes(p.minute); d.setSeconds(0, 0)
    onChange(d)
  }
  const pickCustom = () => {
    setTimeMode('custom'); onAnyTime?.(false)
  }
  const setCustomTime = (str) => {
    if (!str) return
    const [hh, mm] = str.split(':').map(n => parseInt(n, 10))
    const d = new Date(value || new Date())
    d.setHours(hh || 0); d.setMinutes(mm || 0); d.setSeconds(0, 0)
    onChange(d)
  }

  return (
    <div>
      {/* ── DAY ───────────────────────────────────────────────── */}
      <div className="mono-label sublabel">Day</div>
      <div className="day-row">
        <button
          className={'day-chip' + (!anyTime && dayMode === 'today' ? ' active' : '')}
          onClick={pickToday}
        >Today</button>
        <button
          className={'day-chip' + (!anyTime && dayMode === 'tomorrow' ? ' active' : '')}
          onClick={pickTomorrow}
        >Tomorrow</button>
        <button
          className={'day-chip' + (!anyTime && dayMode === 'select' ? ' active' : '')}
          onClick={pickSelectDay}
        >Select day</button>
        <button
          className={'any-time-btn' + (anyTime ? ' active' : '')}
          onClick={() => onAnyTime?.(!anyTime)}
          title="Don't filter by opening hours"
        >{anyTime ? '✓ Any time' : 'Any time'}</button>
      </div>

      {dayMode === 'select' && !anyTime && (
        <div className="weekday-row">
          {WEEKDAYS.map((w, i) => (
            <button
              key={w}
              className={'weekday-chip' + (selectedWeekday === i ? ' active' : '')}
              onClick={() => pickWeekday(i)}
            >{w}</button>
          ))}
        </div>
      )}

      {/* ── TIME ──────────────────────────────────────────────── */}
      <div className={'mono-label sublabel' + (anyTime ? ' dim' : '')} style={{ marginTop: 22 }}>Time</div>
      <div className={'day-row' + (anyTime ? ' disabled' : '')}>
        {MEAL_PRESETS.map((p) => (
          <button
            key={p.key}
            className={'day-chip' + (!anyTime && timeMode === p.key ? ' active' : '')}
            onClick={() => pickMeal(p)}
          >{p.label} ({p.hour === 12 ? '12PM' : p.hour < 12 ? `${p.hour}AM` : `${p.hour - 12}PM`})</button>
        ))}
        <button
          className={'day-chip' + (!anyTime && timeMode === 'custom' ? ' active' : '')}
          onClick={pickCustom}
        >Custom</button>
      </div>

      {timeMode === 'custom' && !anyTime && (
        <div className="weekday-row">
          <input
            type="time"
            className="weekday-chip time-input"
            value={timeStr}
            onChange={(e) => setCustomTime(e.target.value)}
          />
        </div>
      )}
    </div>
  )
}
