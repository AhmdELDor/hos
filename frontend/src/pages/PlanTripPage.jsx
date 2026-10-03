import { useState } from 'react'
import { planDrive } from '../api.js'
import CycleHoursInput from '../components/CycleHoursInput.jsx'
import LocationSearch from '../components/LocationSearch.jsx'
import SiteHeader from '../components/SiteHeader.jsx'
import { BoxIcon, CoffeeIcon, FlagIcon, FuelPumpIcon, MoonIcon, SteeringWheelIcon, TruckIcon } from '../components/icons.jsx'
import { readServerErrors, validateTrip } from '../validation.js'

const FIELD_IDS = {
  currentLocation: 'current-location',
  pickupLocation: 'pickup-location',
  dropoffLocation: 'dropoff-location',
  cycleUsed: 'cycle-used',
}

const RULES = [
  { Icon: SteeringWheelIcon, text: 'Up to 11 hours of driving after 10 hours off' },
  { Icon: CoffeeIcon, text: 'A 30-minute break after 8 hours behind the wheel' },
  { Icon: MoonIcon, text: 'No driving past the 14th hour of the duty day' },
  { Icon: FuelPumpIcon, text: 'A fuel stop at least every 1,000 miles' },
]

function toRequestLocation(location) {
  return {
    lat: location.lat,
    lng: location.lng,
    name: location.name,
  }
}

function buildTripRequest(form) {
  return {
    current_location: toRequestLocation(form.currentLocation),
    pickup_location: toRequestLocation(form.pickupLocation),
    dropoff_location: toRequestLocation(form.dropoffLocation),
    cycle_used: Number(form.cycleUsed),
  }
}

function focusFirstInvalidField(errors) {
  for (const fieldName in FIELD_IDS) {
    if (errors[fieldName]) {
      document.getElementById(FIELD_IDS[fieldName]).focus()
      return
    }
  }
}

export default function PlanTripPage({ form, setForm, onTripPlanned }) {
  const [fieldErrors, setFieldErrors] = useState({})
  const [formError, setFormError] = useState('')
  const [hasTriedSubmit, setHasTriedSubmit] = useState(false)
  const [isPlanning, setIsPlanning] = useState(false)

  function updateField(fieldName, value) {
    const nextForm = { ...form, [fieldName]: value }
    setForm(nextForm)

    if (hasTriedSubmit) {
      setFieldErrors(validateTrip(nextForm))
    }
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setHasTriedSubmit(true)
    setFormError('')

    const errors = validateTrip(form)
    setFieldErrors(errors)

    if (Object.keys(errors).length > 0) {
      focusFirstInvalidField(errors)
      return
    }

    setIsPlanning(true)

    try {
      const trip = await planDrive(buildTripRequest(form))
      setIsPlanning(false)
      onTripPlanned(trip)
    } catch (error) {
      const serverErrors = readServerErrors(error.details)
      setFieldErrors(serverErrors)
      setFormError(serverErrors.form || error.message)
      setIsPlanning(false)
    }
  }

  return (
    <div className="page plan-page">
      <SiteHeader />

      <main className="plan-layout">
        <section className="intro" aria-labelledby="intro-title">
          <h1 id="intro-title" className="intro__title">
            Plan the haul, hour by hour.
          </h1>
          <p className="intro__text">
            Tell us where the truck is, where the load waits and where it goes. You get the route on a map, every fuel
            stop, break and rest, and a filled-in daily log for each day on the road.
          </p>

          <ul className="rules">
            {RULES.map(({ Icon, text }) => (
              <li key={text} className="rules__item">
                <Icon className="rules__icon" />
                <span>{text}</span>
              </li>
            ))}
          </ul>

          <p className="intro__note">
            Built for property-carrying drivers on the 70-hour, 8-day schedule.
          </p>
        </section>

        <section className="trip-card" aria-labelledby="trip-card-title">
          <h2 id="trip-card-title" className="trip-card__title">
            Your trip
          </h2>

          <form className="trip-form" onSubmit={handleSubmit} noValidate>
            <fieldset className="route" disabled={isPlanning}>
              <legend className="visually-hidden">Route</legend>

              <LocationSearch
                id={FIELD_IDS.currentLocation}
                label="Where is the truck now?"
                mapTitle="Where is the truck now?"
                hint="Your starting point for today."
                marker={<TruckIcon />}
                value={form.currentLocation}
                onChange={(location) => updateField('currentLocation', location)}
                error={fieldErrors.currentLocation}
                disabled={isPlanning}
              />

              <LocationSearch
                id={FIELD_IDS.pickupLocation}
                label="Pickup"
                mapTitle="Choose the pickup location"
                hint="Where you load. We plan 1 hour here."
                marker={<BoxIcon />}
                value={form.pickupLocation}
                onChange={(location) => updateField('pickupLocation', location)}
                error={fieldErrors.pickupLocation}
                disabled={isPlanning}
              />

              <LocationSearch
                id={FIELD_IDS.dropoffLocation}
                label="Dropoff"
                mapTitle="Choose the dropoff location"
                hint="Where you deliver. We plan 1 hour here too."
                marker={<FlagIcon />}
                value={form.dropoffLocation}
                onChange={(location) => updateField('dropoffLocation', location)}
                error={fieldErrors.dropoffLocation}
                disabled={isPlanning}
              />
            </fieldset>

            <CycleHoursInput
              id={FIELD_IDS.cycleUsed}
              value={form.cycleUsed}
              onChange={(value) => updateField('cycleUsed', value)}
              error={fieldErrors.cycleUsed}
              disabled={isPlanning}
            />

            {formError && (
              <div className="form-alert" role="alert">
                {formError}
              </div>
            )}

            <button className="plan-button" type="submit" disabled={isPlanning}>
              {isPlanning && <span className="plan-button__spinner" aria-hidden="true" />}
              {isPlanning ? 'Planning trip…' : 'Plan trip'}
            </button>

            <p className="plan-status" role="status">
              {isPlanning ? 'Finding the route and fuel stations. This takes a few seconds.' : ''}
            </p>
          </form>
        </section>
      </main>
    </div>
  )
}
