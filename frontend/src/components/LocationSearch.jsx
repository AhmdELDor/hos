import { useState } from 'react'
import { MapPinIcon } from './icons.jsx'
import MapPicker from './MapPicker.jsx'
import SearchCombobox from './SearchCombobox.jsx'

export default function LocationSearch({ id, label, mapTitle, hint, marker, value, onChange, error, disabled }) {
  const [text, setText] = useState(value ? value.name : '')
  const [isPickingOnMap, setIsPickingOnMap] = useState(false)

  const hintId = `${id}-hint`
  const errorId = `${id}-error`
  const isChosen = value !== null && value.name === text
  const describedBy = error ? `${hintId} ${errorId}` : hintId

  function handleTextChange(newText) {
    setText(newText)
    if (value !== null) {
      onChange(null)
    }
  }

  function chooseLocation(location) {
    setText(location.name)
    onChange(location)
  }

  function pickFromMap(location) {
    setIsPickingOnMap(false)
    chooseLocation(location)
  }

  return (
    <div className="route-stop">
      <div className="route-stop__marker">{marker}</div>

      <div className="field">
        <div className="field__label-row">
          <label className="field__label" htmlFor={id}>
            {label}
          </label>
          <button className="map-link-button" type="button" disabled={disabled} onClick={() => setIsPickingOnMap(true)}>
            <MapPinIcon />
            Choose on map
          </button>
        </div>

        <SearchCombobox
          id={id}
          text={text}
          onTextChange={handleTextChange}
          onChoose={chooseLocation}
          isChosen={isChosen}
          placeholder="City, address or place"
          describedBy={describedBy}
          isInvalid={Boolean(error)}
          disabled={disabled}
        />

        <p id={hintId} className="field__hint">
          {hint}
        </p>

        {error && (
          <p id={errorId} className="field__error">
            {error}
          </p>
        )}
      </div>

      {isPickingOnMap && (
        <MapPicker
          title={mapTitle}
          startLocation={value}
          onPick={pickFromMap}
          onClose={() => setIsPickingOnMap(false)}
        />
      )}
    </div>
  )
}
