import LogSheet from '../components/LogSheet.jsx'
import RouteMap from '../components/RouteMap.jsx'
import SiteHeader from '../components/SiteHeader.jsx'
import StopList from '../components/StopList.jsx'
import { collectStops, shortenPlaceName } from '../stopTypes.js'
import { formatDayTime, formatDuration } from '../time.js'

function sumDrivingHours(segments) {
  let hours = 0
  for (const segment of segments) {
    if (segment.status === 'driving') {
      hours = hours + segment.hours
    }
  }
  return hours
}

export default function TripResultPage({ trip, onEditTrip }) {
  const stops = collectStops(trip)
  const lastSegment = trip.segments[trip.segments.length - 1]
  const fromName = shortenPlaceName(trip.locations.current.name || 'Start')
  const pickupName = shortenPlaceName(trip.locations.pickup.name || 'Pickup')
  const dropoffName = shortenPlaceName(trip.locations.dropoff.name || 'Dropoff')
  const totalDays = trip.daily_logs.length

  return (
    <div className="page result-page">
      <SiteHeader>
        <button className="ghost-button" type="button" onClick={onEditTrip}>
          Edit trip
        </button>
      </SiteHeader>

      <main>
        <section className="trip-summary" aria-labelledby="trip-summary-title">
          <h1 id="trip-summary-title" className="trip-summary__title">
            {fromName} to {dropoffName}
          </h1>
          <p className="trip-summary__via">Picking up in {pickupName}</p>

          <dl className="trip-summary__facts">
            <div>
              <dt>Distance</dt>
              <dd>{Math.round(trip.full_legs_miles).toLocaleString('en-US')} miles</dd>
            </div>
            <div>
              <dt>Driving time</dt>
              <dd>{formatDuration(sumDrivingHours(trip.segments))}</dd>
            </div>
            <div>
              <dt>Leaves</dt>
              <dd>{formatDayTime(trip.start_time)}</dd>
            </div>
            <div>
              <dt>Done</dt>
              <dd>{formatDayTime(lastSegment.end)}</dd>
            </div>
            <div>
              <dt>Log sheets</dt>
              <dd>{totalDays}</dd>
            </div>
          </dl>
        </section>

        <section className="route-section" aria-labelledby="route-title">
          <h2 id="route-title" className="visually-hidden">
            Route and stops
          </h2>
          <div className="route-section__map">
            <RouteMap routePoints={trip.route_points} stops={stops} />
          </div>

          <div className="route-section__stops">
            <h2 className="section-title">Stops in order</h2>
            <StopList stops={stops} />
          </div>
        </section>

        <section className="logs-section" aria-labelledby="logs-title">
          <div className="logs-section__header">
            <div>
              <h2 id="logs-title" className="section-title">
                Daily logs
              </h2>
              <p className="logs-section__note">
                Times use the clock where the trip starts. Each sheet adds up to 24 hours.
              </p>
            </div>
            <button className="ghost-button" type="button" onClick={() => window.print()}>
              Print logs
            </button>
          </div>

          {trip.daily_logs.map((log, index) => (
            <LogSheet key={log.date} log={log} dayNumber={index + 1} totalDays={totalDays} />
          ))}
        </section>
      </main>
    </div>
  )
}
