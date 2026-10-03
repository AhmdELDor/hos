import { useEffect, useState } from 'react'
import { searchLocations } from '../api.js'

const SEARCH_DELAY_MS = 350
const MIN_SEARCH_LETTERS = 3

export default function SearchCombobox({
  id,
  text,
  onTextChange,
  onChoose,
  isChosen,
  placeholder,
  describedBy,
  isInvalid,
  disabled,
  ariaLabel,
}) {
  const [suggestions, setSuggestions] = useState([])
  const [isOpen, setIsOpen] = useState(false)
  const [activeIndex, setActiveIndex] = useState(-1)
  const [isSearching, setIsSearching] = useState(false)
  const [searchError, setSearchError] = useState('')
  const [lastSearchedText, setLastSearchedText] = useState('')

  const listId = `${id}-suggestions`
  const searchText = text.trim()

  useEffect(() => {
    if (isChosen || searchText.length < MIN_SEARCH_LETTERS) {
      return
    }

    const controller = new AbortController()

    const timer = setTimeout(async () => {
      setIsSearching(true)
      setSearchError('')

      try {
        const locations = await searchLocations(searchText, controller.signal)
        setSuggestions(locations)
        setLastSearchedText(searchText)
        setActiveIndex(-1)
        setIsOpen(true)
      } catch (searchFailure) {
        if (searchFailure.name !== 'AbortError') {
          setSuggestions([])
          setLastSearchedText(searchText)
          setSearchError(searchFailure.message)
          setIsOpen(true)
        }
      } finally {
        setIsSearching(false)
      }
    }, SEARCH_DELAY_MS)

    return () => {
      clearTimeout(timer)
      controller.abort()
    }
  }, [searchText, isChosen])

  const hasFinishedSearch = lastSearchedText === searchText
  const hasSomethingToShow = suggestions.length > 0 || hasFinishedSearch
  const showList = isOpen && !isChosen && searchText.length >= MIN_SEARCH_LETTERS && hasSomethingToShow

  function handleTextChange(event) {
    onTextChange(event.target.value)
    if (event.target.value.trim().length < MIN_SEARCH_LETTERS) {
      setSuggestions([])
      setIsOpen(false)
    }
  }

  function chooseLocation(location) {
    setSuggestions([])
    setIsOpen(false)
    setActiveIndex(-1)
    onChoose(location)
  }

  function handleKeyDown(event) {
    if (event.key === 'ArrowDown' && suggestions.length > 0) {
      event.preventDefault()
      setIsOpen(true)
      setActiveIndex((activeIndex + 1) % suggestions.length)
    } else if (event.key === 'ArrowUp' && suggestions.length > 0) {
      event.preventDefault()
      setActiveIndex(activeIndex <= 0 ? suggestions.length - 1 : activeIndex - 1)
    } else if (event.key === 'Enter' && isOpen && activeIndex >= 0) {
      event.preventDefault()
      chooseLocation(suggestions[activeIndex])
    } else if (event.key === 'Escape' && showList) {
      event.preventDefault()
      setIsOpen(false)
    }
  }

  let activeOptionId
  if (activeIndex >= 0) {
    activeOptionId = `${id}-option-${activeIndex}`
  }

  let inputClassName = 'text-input'
  if (isInvalid) {
    inputClassName = 'text-input text-input--invalid'
  }

  return (
    <div className="location-search">
      <input
        id={id}
        className={inputClassName}
        type="text"
        role="combobox"
        autoComplete="off"
        spellCheck="false"
        placeholder={placeholder}
        value={text}
        disabled={disabled}
        aria-label={ariaLabel}
        aria-autocomplete="list"
        aria-expanded={showList}
        aria-controls={listId}
        aria-activedescendant={activeOptionId}
        aria-invalid={isInvalid ? 'true' : 'false'}
        aria-describedby={describedBy}
        onChange={handleTextChange}
        onKeyDown={handleKeyDown}
        onFocus={() => setIsOpen(true)}
        onBlur={() => setIsOpen(false)}
      />

      {isSearching && <span className="input-spinner" aria-hidden="true" />}
      {isChosen && <span className="input-check" aria-hidden="true" />}

      <ul id={listId} className="suggestions" role="listbox" hidden={!showList}>
        {suggestions.map((location, index) => {
          let optionClassName = 'suggestion'
          if (index === activeIndex) {
            optionClassName = 'suggestion suggestion--active'
          }

          return (
            <li
              key={`${location.lat},${location.lng},${index}`}
              id={`${id}-option-${index}`}
              className={optionClassName}
              role="option"
              aria-selected={index === activeIndex}
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => chooseLocation(location)}
            >
              {location.name}
            </li>
          )
        })}

        {hasFinishedSearch && suggestions.length === 0 && !searchError && (
          <li className="suggestion suggestion--empty" role="presentation">
            No places found. Try a city and state, like Dallas, TX.
          </li>
        )}

        {searchError && (
          <li className="suggestion suggestion--empty" role="presentation">
            {searchError}
          </li>
        )}
      </ul>
    </div>
  )
}
