export function formatDayTime(isoText) {
  const date = new Date(isoText)
  return date.toLocaleString('en-US', {
    weekday: 'short',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  })
}

export function formatClock(isoText) {
  const date = new Date(isoText)
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  })
}

export function hoursIntoDay(isoText, dayText) {
  const parts = isoText.split('T')
  const datePart = parts[0]
  const timePart = parts[1]

  if (datePart !== dayText) {
    return 24
  }

  const timePieces = timePart.split(':')
  const hours = Number(timePieces[0])
  const minutes = Number(timePieces[1])
  const seconds = parseFloat(timePieces[2] || '0')

  return hours + minutes / 60 + seconds / 3600
}

export function formatHours(hours) {
  const roundedHours = Math.round(hours * 100) / 100
  return String(roundedHours)
}

export function formatDuration(hours) {
  const totalMinutes = Math.round(hours * 60)
  const wholeHours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60

  if (minutes === 0) {
    return `${wholeHours} h`
  }
  return `${wholeHours} h ${minutes} min`
}

export function splitDay(dayText) {
  const parts = dayText.split('-')
  return { year: parts[0], month: parts[1], day: parts[2] }
}
