import L from 'leaflet'
import { renderToStaticMarkup } from 'react-dom/server'
import { MapContainer, Marker, Polyline, Popup, TileLayer } from 'react-leaflet'
import { STOP_TYPES } from '../stopTypes.js'
import { formatDayTime } from '../time.js'

function makeMarkerIcon(stopType) {
  const Icon = STOP_TYPES[stopType].Icon
  const iconMarkup = renderToStaticMarkup(<Icon />)

  return L.divIcon({
    className: 'stop-marker-holder',
    html: `<span class="stop-marker stop-marker--${stopType}">${iconMarkup}</span>`,
    iconSize: [34, 34],
    iconAnchor: [17, 17],
    popupAnchor: [0, -18],
  })
}

const MARKER_ICONS = {}
for (const stopType in STOP_TYPES) {
  MARKER_ICONS[stopType] = makeMarkerIcon(stopType)
}

function toLatLngs(routePoints) {
  const latLngs = []
  for (const point of routePoints) {
    latLngs.push([point[1], point[0]])
  }
  return latLngs
}

export default function RouteMap({ routePoints, stops }) {
  const latLngs = toLatLngs(routePoints)
  const bounds = L.latLngBounds(latLngs)

  return (
    <MapContainer bounds={bounds} boundsOptions={{ padding: [36, 36] }} scrollWheelZoom={false} className="route-map">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <Polyline positions={latLngs} pathOptions={{ color: '#16253d', weight: 9, opacity: 0.2 }} />
      <Polyline positions={latLngs} pathOptions={{ color: '#1f4aa8', weight: 5, opacity: 0.95 }} />

      {stops.map((stop, index) => (
        <Marker key={`${stop.type}-${index}`} position={[stop.lat, stop.lng]} icon={MARKER_ICONS[stop.type]}>
          <Popup>
            <div className="map-popup">
              <strong>{STOP_TYPES[stop.type].label}</strong>
              <span>{stop.place || stop.name}</span>
              {stop.type === 'fuel' && stop.name !== 'Fuel stop' && <span>{stop.name}</span>}
              <span className="map-popup__time">
                {formatDayTime(stop.start)}
                {stop.end !== stop.start && ` to ${formatDayTime(stop.end)}`}
              </span>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  )
}
