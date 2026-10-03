import { useState } from 'react'
import RoadBackground from './components/RoadBackground.jsx'
import PlanTripPage from './pages/PlanTripPage.jsx'
import TripResultPage from './pages/TripResultPage.jsx'

const EMPTY_FORM = {
  currentLocation: null,
  pickupLocation: null,
  dropoffLocation: null,
  cycleUsed: '',
}

export default function App() {
  const [form, setForm] = useState(EMPTY_FORM)
  const [trip, setTrip] = useState(null)

  function showTrip(plannedTrip) {
    setTrip(plannedTrip)
    window.scrollTo(0, 0)
  }

  function editTrip() {
    setTrip(null)
    window.scrollTo(0, 0)
  }

  return (
    <>
      <RoadBackground showIcons={trip === null} />
      {trip === null ? (
        <PlanTripPage form={form} setForm={setForm} onTripPlanned={showTrip} />
      ) : (
        <TripResultPage trip={trip} onEditTrip={editTrip} />
      )}
    </>
  )
}
