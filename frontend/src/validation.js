const MAX_CYCLE_HOURS = 70

function isSamePlace(firstLocation, secondLocation) {
  return firstLocation.lat === secondLocation.lat && firstLocation.lng === secondLocation.lng
}

export function validateTrip(form) {
  const errors = {}

  if (form.currentLocation === null) {
    errors.currentLocation = 'Choose where the truck is now from the list.'
  }

  if (form.pickupLocation === null) {
    errors.pickupLocation = 'Choose the pickup location from the list.'
  }

  if (form.dropoffLocation === null) {
    errors.dropoffLocation = 'Choose the dropoff location from the list.'
  }

  if (form.pickupLocation !== null && form.dropoffLocation !== null) {
    if (isSamePlace(form.pickupLocation, form.dropoffLocation)) {
      errors.dropoffLocation = 'Dropoff must be a different place from pickup.'
    }
  }

  if (form.cycleUsed === '') {
    errors.cycleUsed = 'Enter the hours already used this cycle. Use 0 for a fresh cycle.'
  } else {
    const hours = Number(form.cycleUsed)
    if (Number.isNaN(hours) || hours < 0 || hours > MAX_CYCLE_HOURS) {
      errors.cycleUsed = 'Enter a number of hours from 0 to 70.'
    }
  }

  return errors
}

const SERVER_FIELD_NAMES = {
  current_location: 'currentLocation',
  pickup_location: 'pickupLocation',
  dropoff_location: 'dropoffLocation',
  cycle_used: 'cycleUsed',
}

export function readServerErrors(details) {
  const fieldErrors = {}

  if (!details) {
    return fieldErrors
  }

  for (const serverName in SERVER_FIELD_NAMES) {
    const detail = details[serverName]
    if (!detail) {
      continue
    }

    const fieldName = SERVER_FIELD_NAMES[serverName]
    if (Array.isArray(detail)) {
      fieldErrors[fieldName] = detail[0]
    } else {
      fieldErrors[fieldName] = 'This location could not be used. Choose it again from the list.'
    }
  }

  if (details.non_field_errors) {
    fieldErrors.form = details.non_field_errors[0]
  }

  return fieldErrors
}
