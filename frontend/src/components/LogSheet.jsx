import { formatHours, hoursIntoDay, splitDay } from '../time.js'

const VIEW_WIDTH = 1000
const GRID_LEFT = 132
const HOUR_WIDTH = 32
const GRID_RIGHT = GRID_LEFT + 24 * HOUR_WIDTH
const TOTALS_CENTER = 950
const BAND_TOP = 6
const BAND_HEIGHT = 30
const GRID_TOP = BAND_TOP + BAND_HEIGHT
const ROW_HEIGHT = 38
const GRID_BOTTOM = GRID_TOP + 4 * ROW_HEIGHT
const REMARK_LABEL_GAP = 15
const VIEW_HEIGHT = GRID_BOTTOM + 150
const BAND_OVERHANG = 26

const HOURS = []
for (let hour = 0; hour <= 24; hour++) {
  HOURS.push(hour)
}

const ROWS = [
  { status: 'off_duty', number: '1', label: 'Off duty' },
  { status: 'sleeper_berth', number: '2', label: 'Sleeper berth' },
  { status: 'driving', number: '3', label: 'Driving' },
  { status: 'on_duty', number: '4', label: 'On duty', subLabel: '(not driving)' },
]

const SHORT_NOTES = {
  'Pre-trip inspection': 'pre-trip',
  'Post-trip inspection': 'post-trip',
  Driving: 'driving',
  Pickup: 'pickup',
  Dropoff: 'dropoff',
  'Fuel stop': 'fuel',
  'Break after fuel': 'break',
  '30-minute break': 'break',
  '10-hour rest': 'sleeper',
  '34-hour restart': 'restart',
  'Off duty': 'off duty',
}

function hourToX(hours) {
  return GRID_LEFT + hours * HOUR_WIDTH
}

function rowCenterY(status) {
  let rowIndex = 0
  for (let index = 0; index < ROWS.length; index++) {
    if (ROWS[index].status === status) {
      rowIndex = index
    }
  }
  return GRID_TOP + rowIndex * ROW_HEIGHT + ROW_HEIGHT / 2
}

function hourLabel(hour) {
  if (hour === 0 || hour === 24) {
    return 'Midnight'
  }
  if (hour === 12) {
    return 'Noon'
  }
  if (hour > 12) {
    return String(hour - 12)
  }
  return String(hour)
}

function buildDutyLinePoints(log) {
  const points = []

  for (const piece of log.segments) {
    const startX = hourToX(hoursIntoDay(piece.start, log.date))
    const endX = hourToX(hoursIntoDay(piece.end, log.date))
    const y = rowCenterY(piece.status)
    points.push(`${startX},${y}`)
    points.push(`${endX},${y}`)
  }

  return points.join(' ')
}

function buildRemarkLabels(log) {
  const labels = []
  let previousLabelX = -100

  for (const remark of log.remarks) {
    const tickX = hourToX(hoursIntoDay(remark.time, log.date))
    const labelX = Math.max(tickX, previousLabelX + REMARK_LABEL_GAP)
    previousLabelX = labelX

    let place = `${remark.lat.toFixed(2)}, ${remark.lng.toFixed(2)}`
    if (remark.place) {
      place = remark.place
    }

    labels.push({
      tickX: tickX,
      labelX: labelX,
      place: place,
      note: SHORT_NOTES[remark.note] || remark.note.toLowerCase(),
    })
  }

  return labels
}

function GridTicks() {
  const lines = []

  for (let rowIndex = 0; rowIndex < ROWS.length; rowIndex++) {
    const rowTop = GRID_TOP + rowIndex * ROW_HEIGHT

    for (let hour = 0; hour < 24; hour++) {
      const quarterTicks = [
        { offset: 0.25, length: 9 },
        { offset: 0.5, length: 16 },
        { offset: 0.75, length: 9 },
      ]

      for (const tick of quarterTicks) {
        const x = hourToX(hour + tick.offset)
        lines.push(<line key={`${rowIndex}-${hour}-${tick.offset}`} x1={x} y1={rowTop} x2={x} y2={rowTop + tick.length} />)
      }
    }
  }

  for (let hour = 0; hour <= 24; hour++) {
    const x = hourToX(hour)
    lines.push(<line key={`hour-${hour}`} className="log-grid__hour-line" x1={x} y1={GRID_TOP} x2={x} y2={GRID_BOTTOM} />)
  }

  return <g className="log-grid__ticks">{lines}</g>
}

function DutyGrid({ log }) {
  const remarkLabels = buildRemarkLabels(log)

  return (
    <svg
      className="log-grid"
      viewBox={`0 0 ${VIEW_WIDTH} ${VIEW_HEIGHT}`}
      role="img"
      aria-label={`Duty status graph for ${log.date}`}
    >
      <rect
        className="log-grid__band"
        x={GRID_LEFT - BAND_OVERHANG}
        y={BAND_TOP}
        width={GRID_RIGHT - GRID_LEFT + 2 * BAND_OVERHANG}
        height={BAND_HEIGHT}
        rx="3"
      />
      {HOURS.map((hour) => (
        <text
          key={hour}
          className="log-grid__band-text"
          x={hourToX(hour)}
          y={BAND_TOP + BAND_HEIGHT / 2 + 4}
          textAnchor="middle"
        >
          {hourLabel(hour)}
        </text>
      ))}
      <text className="log-grid__totals-title" x={TOTALS_CENTER + 6} y={BAND_TOP + 13} textAnchor="middle">
        Total
      </text>
      <text className="log-grid__totals-title" x={TOTALS_CENTER + 6} y={BAND_TOP + 26} textAnchor="middle">
        hours
      </text>

      {ROWS.map((row, index) => {
        const rowTop = GRID_TOP + index * ROW_HEIGHT
        return (
          <g key={row.status}>
            <rect className="log-grid__row" x={GRID_LEFT} y={rowTop} width={GRID_RIGHT - GRID_LEFT} height={ROW_HEIGHT} />
            <text className="log-grid__row-label" x={8} y={rowTop + (row.subLabel ? 17 : 24)}>
              {row.number}. {row.label}
            </text>
            {row.subLabel && (
              <text className="log-grid__row-sublabel" x={22} y={rowTop + 31}>
                {row.subLabel}
              </text>
            )}
            <text className="log-grid__total" x={TOTALS_CENTER} y={rowTop + 25} textAnchor="middle">
              {formatHours(log.totals[row.status])}
            </text>
            <line className="log-grid__total-line" x1={TOTALS_CENTER - 34} y1={rowTop + 31} x2={TOTALS_CENTER + 34} y2={rowTop + 31} />
          </g>
        )
      })}

      <GridTicks />

      <text className="log-grid__total log-grid__total--sum" x={TOTALS_CENTER} y={GRID_BOTTOM + 24} textAnchor="middle">
        = {formatHours(log.total_hours)}
      </text>

      <polyline className="log-grid__duty-line" points={buildDutyLinePoints(log)} />

      <text className="log-grid__remarks-title" x={8} y={GRID_BOTTOM + 24}>
        Remarks
      </text>

      {remarkLabels.map((label, index) => (
        <g key={index} className="log-grid__remark">
          <line x1={label.tickX} y1={GRID_BOTTOM} x2={label.tickX} y2={GRID_BOTTOM + 10} />
          <line x1={label.tickX} y1={GRID_BOTTOM + 10} x2={label.labelX} y2={GRID_BOTTOM + 16} />
          <text transform={`translate(${label.labelX} ${GRID_BOTTOM + 20}) rotate(52)`}>
            <tspan className="log-grid__remark-place">{label.place}</tspan>
            <tspan className="log-grid__remark-note" dx="5">
              {label.note}
            </tspan>
          </text>
        </g>
      ))}
    </svg>
  )
}

function FormField({ label, value, wide }) {
  let className = 'log-field'
  if (wide) {
    className = 'log-field log-field--wide'
  }

  return (
    <div className={className}>
      <span className="log-field__value">{value}</span>
      <span className="log-field__label">{label}</span>
    </div>
  )
}

export default function LogSheet({ log, dayNumber, totalDays }) {
  const date = splitDay(log.date)
  const firstRemark = log.remarks[0]
  const lastRemark = log.remarks[log.remarks.length - 1]

  let fromPlace = log.segments[0].place || ''
  let toPlace = log.segments[log.segments.length - 1].place || ''
  if (firstRemark && firstRemark.place) {
    fromPlace = firstRemark.place
  }
  if (lastRemark && lastRemark.place) {
    toPlace = lastRemark.place
  }

  return (
    <article className="log-sheet" aria-labelledby={`log-title-${log.date}`}>
      <header className="log-sheet__header">
        <div className="log-sheet__title-block">
          <h3 id={`log-title-${log.date}`} className="log-sheet__title">
            Driver's daily log
          </h3>
          <span className="log-sheet__subtitle">
            Day {dayNumber} of {totalDays}, one calendar day (24 hours)
          </span>
        </div>

        <div className="log-sheet__date" aria-label={`Date ${log.date}`}>
          <FormField label="month" value={date.month} />
          <span className="log-sheet__date-slash">/</span>
          <FormField label="day" value={date.day} />
          <span className="log-sheet__date-slash">/</span>
          <FormField label="year" value={date.year} />
        </div>
      </header>

      <div className="log-sheet__fields">
        <FormField label="From" value={fromPlace} wide />
        <FormField label="To" value={toPlace} wide />
        <FormField label="Total miles driving today" value={Math.round(log.miles_today)} />
        <FormField label="Name of carrier" value="" wide />
        <FormField label="Truck / trailer numbers" value="" />
        <FormField label="Main office address" value="" wide />
      </div>

      <div className="log-sheet__grid-scroll">
        <DutyGrid log={log} />
      </div>

      <footer className="log-sheet__recap">
        <span className="log-sheet__recap-title">Recap, 70 hours in 8 days</span>
        <dl className="log-sheet__recap-values">
          <div>
            <dt>On duty today</dt>
            <dd>{formatHours(log.recap.on_duty_today)} h</dd>
          </div>
          <div>
            <dt>Total on duty, last 8 days</dt>
            <dd>{formatHours(log.recap.total_last_8_days)} h</dd>
          </div>
          <div>
            <dt>Available tomorrow</dt>
            <dd>{formatHours(log.recap.available_tomorrow)} h</dd>
          </div>
        </dl>
      </footer>
    </article>
  )
}
