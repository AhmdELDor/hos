const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const UNREACHABLE_MESSAGE = "Can't reach the trip planner. Make sure the backend is running, then try again."

async function readResponse(response) {
  let body = null

  try {
    body = await response.json()
  } catch {
    body = null
  }

  if (response.ok && body && body.success) {
    return body.data
  }

  let message = 'The planner sent an unexpected reply. Try again.'
  let details = null

  if (body && body.error) {
    message = body.error.message
    details = body.error.details
  }

  const error = new Error(message)
  error.details = details
  throw error
}

export async function searchLocations(text, signal) {
  const url = `${API_URL}/api/search-location/?text=${encodeURIComponent(text)}`
  let response

  try {
    response = await fetch(url, { signal })
  } catch (error) {
    if (error.name === 'AbortError') {
      throw error
    }
    throw new Error("Can't reach the location search right now.")
  }

  return readResponse(response)
}

export async function reverseLocation(lat, lng, signal) {
  const url = `${API_URL}/api/reverse-location/?lat=${lat}&lng=${lng}`
  let response

  try {
    response = await fetch(url, { signal })
  } catch (error) {
    if (error.name === 'AbortError') {
      throw error
    }
    throw new Error("Can't reach the location search right now.")
  }

  return readResponse(response)
}

export async function planDrive(tripRequest) {
  let response

  try {
    response = await fetch(`${API_URL}/api/plan-drive/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(tripRequest),
    })
  } catch {
    throw new Error(UNREACHABLE_MESSAGE)
  }

  return readResponse(response)
}
