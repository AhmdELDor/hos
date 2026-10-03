import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from 'react-leaflet'
import { reverseLocation } from '../api.js'
import SearchCombobox from './SearchCombobox.jsx'

const UNITED_STATES_CENTER = [39.5, -98.35]
const UNITED_STATES_ZOOM = 4
const CLOSE_ZOOM = 11
const SEARCH_RESULT_ZOOM = 13

const PIN_SVG = `
  <svg viewBox="0 0 48 48" width="36" height="36" aria-hidden="true">
    <path d="M24 44S10 30.5 10 19.5a14 14 0 0 1 28 0C38 30.5 24 44 24 44z" fill="#1f4aa8" stroke="#16253d" stroke-width="2" />
    <circle cx="24" cy="19.5" r="5" fill="#fbfcfa" />
  </svg>
`

const pinIcon = L.divIcon({
  className: 'map-pin',
  html: PIN_SVG,
  iconSize: [36, 36],
  iconAnchor: [18, 34],
})

function roundCoordinate(value) {
  return Math.round(value * 1000000) / 1000000
}

function formatCoordinates(lat, lng) {
  return `${lat.toFixed(4)}, ${lng.toFixed(4)}`
}

function FitMapToDialog() {
  const map = useMap()

  useEffect(() => {
    map.invalidateSize()
  }, [map])

  return null
}

function MoveMapTo({ location }) {
  const map = useMap()

  useEffect(() => {
    if (location !== null) {
      map.setView([location.lat, location.lng], SEARCH_RESULT_ZOOM)
    }
  }, [map, location])

  return null
}

function ClickCatcher({ onMapClick }) {
  useMapEvents({
    click(event) {
      onMapClick(event.latlng)
    },
  })
  return null
}

export default function MapPicker({ title, startLocation, onPick, onClose }) {
  const dialogRef = useRef(null)
  const lookupRef = useRef(null)
  const [pickedLocation, setPickedLocation] = useState(startLocation)
  const [isLookingUp, setIsLookingUp] = useState(false)
  const [lookupMessage, setLookupMessage] = useState('')
  const [searchText, setSearchText] = useState('')
  const [chosenSearchText, setChosenSearchText] = useState('')
  const [searchedLocation, setSearchedLocation] = useState(null)

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog.open) {
      dialog.showModal()
    }
    document.getElementById('map-search').focus()
  }, [])

  function chooseSearchResult(location) {
    if (lookupRef.current !== null) {
      lookupRef.current.abort()
    }
    setSearchText(location.name)
    setChosenSearchText(location.name)
    setSearchedLocation(location)
    setPickedLocation(location)
    setIsLookingUp(false)
    setLookupMessage('')
  }

  async function handleMapClick(point) {
    const lat = roundCoordinate(point.lat)
    const lng = roundCoordinate(point.lng)

    if (lookupRef.current !== null) {
      lookupRef.current.abort()
    }
    const controller = new AbortController()
    lookupRef.current = controller

    setPickedLocation({ name: formatCoordinates(lat, lng), lat: lat, lng: lng })
    setIsLookingUp(true)
    setLookupMessage('')

    try {
      const location = await reverseLocation(lat, lng, controller.signal)
      setPickedLocation(location)
      setIsLookingUp(false)
    } catch (error) {
      if (error.name === 'AbortError') {
        return
      }
      setLookupMessage("Couldn't find a place name here. You can still use this point.")
      setIsLookingUp(false)
    }
  }

  function handleCancel(event) {
    event.preventDefault()
    onClose()
  }

  let mapCenter = UNITED_STATES_CENTER
  let mapZoom = UNITED_STATES_ZOOM
  if (startLocation !== null) {
    mapCenter = [startLocation.lat, startLocation.lng]
    mapZoom = CLOSE_ZOOM
  }

  let placeText = 'No point chosen yet'
  if (pickedLocation !== null && isLookingUp) {
    placeText = 'Finding the place name…'
  } else if (pickedLocation !== null) {
    placeText = pickedLocation.name
  }

  return (
    <dialog ref={dialogRef} className="map-dialog" aria-labelledby="map-dialog-title" onCancel={handleCancel}>
      <div className="map-dialog__header">
        <div>
          <h2 id="map-dialog-title" className="map-dialog__title">
            {title}
          </h2>
          <p className="map-dialog__help">Search for a place or click the map to drop a pin. Zoom in to place it exactly.</p>
        </div>
        <button className="close-button" type="button" aria-label="Close map" onClick={onClose}>
          <span aria-hidden="true">×</span>
        </button>
      </div>

      <div className="map-dialog__search">
        <SearchCombobox
          id="map-search"
          text={searchText}
          onTextChange={setSearchText}
          onChoose={chooseSearchResult}
          isChosen={searchText !== '' && searchText === chosenSearchText}
          placeholder="Search a city or address to jump there"
          ariaLabel="Search for a place on the map"
        />
      </div>

      <div className="map-dialog__map">
        <MapContainer center={mapCenter} zoom={mapZoom} scrollWheelZoom={true} className="leaflet-map">
          <FitMapToDialog />
          <MoveMapTo location={searchedLocation} />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <ClickCatcher onMapClick={handleMapClick} />
          {pickedLocation !== null && <Marker position={[pickedLocation.lat, pickedLocation.lng]} icon={pinIcon} />}
        </MapContainer>
      </div>

      <div className="map-dialog__footer">
        <div className="map-dialog__place" aria-live="polite">
          <span className="map-dialog__place-label">Chosen point</span>
          <span className="map-dialog__place-name">{placeText}</span>
          {lookupMessage && <span className="map-dialog__place-note">{lookupMessage}</span>}
        </div>

        <div className="map-dialog__actions">
          <button className="ghost-button" type="button" onClick={onClose}>
            Cancel
          </button>
          <button
            className="action-button"
            type="button"
            disabled={pickedLocation === null || isLookingUp}
            onClick={() => onPick(pickedLocation)}
          >
            Use this location
          </button>
        </div>
      </div>
    </dialog>
  )
}
