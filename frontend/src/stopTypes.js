import {
  BoxIcon,
  ClockIcon,
  CoffeeIcon,
  FlagIcon,
  FuelPumpIcon,
  MoonIcon,
  TruckIcon,
} from './components/icons.jsx'

export const STOP_TYPES = {
  start: { label: 'Start', Icon: TruckIcon },
  pickup: { label: 'Pickup', Icon: BoxIcon },
  dropoff: { label: 'Dropoff', Icon: FlagIcon },
  fuel: { label: 'Fuel stop', Icon: FuelPumpIcon },
  break: { label: '30-minute break', Icon: CoffeeIcon },
  rest: { label: '10-hour rest', Icon: MoonIcon },
  restart: { label: '34-hour restart', Icon: ClockIcon },
}

export function shortenPlaceName(name) {
  return name.replace(/, USA$/, '')
}

export function collectStops(trip) {
  const current = trip.locations.current
  const stops = [
    {
      type: 'start',
      name: shortenPlaceName(current.name || 'Start'),
      place: shortenPlaceName(current.name || 'Start'),
      lat: current.lat,
      lng: current.lng,
      start: trip.start_time,
      end: trip.start_time,
      mile: 0,
    },
  ]

  for (const stopType of ['pickup', 'dropoff', 'fuel', 'break', 'rest', 'restart']) {
    for (const stop of trip.stops[stopType]) {
      if (stop.start) {
        stops.push({ ...stop, type: stopType })
      }
    }
  }

  stops.sort((first, second) => new Date(first.start) - new Date(second.start))
  return stops
}
