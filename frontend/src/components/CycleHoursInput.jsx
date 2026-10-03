import { ClockIcon } from './icons.jsx'

const MAX_CYCLE_HOURS = 70
const RESTART_THRESHOLD_HOURS = 0.5
const GAUGE_TICKS = [0, 10, 20, 30, 40, 50, 60, 70]

function readHours(value) {
  if (value === '') {
    return null
  }

  const hours = Number(value)
  if (Number.isNaN(hours) || hours < 0 || hours > MAX_CYCLE_HOURS) {
    return null
  }

  return hours
}

function formatHours(hours) {
  const roundedHours = Math.round(hours * 100) / 100
  return String(roundedHours)
}

export default function CycleHoursInput({ id, value, onChange, error, disabled }) {
  const hintId = `${id}-hint`
  const errorId = `${id}-error`
  const gaugeId = `${id}-gauge`
  const hours = readHours(value)

  let usedPercent = 0
  let gaugeText = 'Enter your hours to see what is left'

  if (hours !== null) {
    const hoursLeft = MAX_CYCLE_HOURS - hours
    usedPercent = (hours / MAX_CYCLE_HOURS) * 100

    if (hoursLeft <= RESTART_THRESHOLD_HOURS) {
      gaugeText = 'Cycle used up. The plan starts with a 34-hour restart.'
    } else {
      gaugeText = `${formatHours(hoursLeft)} of 70 hours left in this cycle`
    }
  }

  let inputClassName = 'text-input text-input--hours'
  if (error) {
    inputClassName = 'text-input text-input--hours text-input--invalid'
  }

  let describedBy = `${hintId} ${gaugeId}`
  if (error) {
    describedBy = `${hintId} ${gaugeId} ${errorId}`
  }

  return (
    <div className="cycle-field">
      <div className="field">
        <label className="field__label" htmlFor={id}>
          Hours already used this cycle
        </label>

        <div className="hours-row">
          <span className="hours-row__icon">
            <ClockIcon />
          </span>
          <input
            id={id}
            className={inputClassName}
            type="number"
            inputMode="decimal"
            min="0"
            max="70"
            step="0.25"
            placeholder="0"
            value={value}
            disabled={disabled}
            aria-invalid={error ? 'true' : 'false'}
            aria-describedby={describedBy}
            onChange={(event) => onChange(event.target.value)}
          />
          <span className="hours-row__unit">hours</span>
        </div>

        <p id={hintId} className="field__hint">
          Driving and on-duty hours from the last 8 days, from 0 to 70.
        </p>

        <div className="gauge" aria-hidden="true">
          <div className="gauge__track">
            <div className="gauge__used" style={{ width: `${usedPercent}%` }} />
          </div>
          <div className="gauge__ticks">
            {GAUGE_TICKS.map((tick) => (
              <span key={tick}>{tick}</span>
            ))}
          </div>
        </div>

        <p id={gaugeId} className="gauge__text">
          {gaugeText}
        </p>

        {error && (
          <p id={errorId} className="field__error">
            {error}
          </p>
        )}
      </div>
    </div>
  )
}
