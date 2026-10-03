import { STOP_TYPES } from '../stopTypes.js'
import { formatClock, formatDayTime } from '../time.js'

function describeFuelStop(stop) {
  let description = ''
  if (stop.name !== 'Fuel stop') {
    description = stop.name
  }
  if (stop.stop_type === 'fuel_and_break') {
    description = `${description} Counts as the 30-minute break.`.trim()
  }
  return description
}

function formatStopEnd(stop) {
  const startDay = stop.start.slice(0, 10)
  const endDay = stop.end.slice(0, 10)

  if (startDay === endDay) {
    return formatClock(stop.end)
  }
  return formatDayTime(stop.end)
}

export default function StopList({ stops }) {
  return (
    <ol className="stop-list">
      {stops.map((stop, index) => {
        const { label, Icon } = STOP_TYPES[stop.type]

        return (
          <li key={`${stop.type}-${index}`} className="stop-list__item">
            <span className={`stop-marker stop-marker--${stop.type}`}>
              <Icon />
            </span>

            <div className="stop-list__text">
              <span className="stop-list__title">{label}</span>
              <span className="stop-list__place">{stop.place || stop.name}</span>
              {stop.type === 'fuel' && describeFuelStop(stop) && (
                <span className="stop-list__detail">{describeFuelStop(stop)}</span>
              )}
            </div>

            <div className="stop-list__when">
              <span>{formatDayTime(stop.start)}</span>
              {stop.end !== stop.start && <span className="stop-list__until">to {formatStopEnd(stop)}</span>}
              <span className="stop-list__mile">mile {Math.round(stop.mile)}</span>
            </div>
          </li>
        )
      })}
    </ol>
  )
}
