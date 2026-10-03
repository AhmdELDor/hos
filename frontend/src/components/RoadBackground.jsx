import { useState } from 'react'
import {
  ClockIcon,
  CoffeeIcon,
  ConeIcon,
  FuelPumpIcon,
  MapPinIcon,
  MoonIcon,
  RoadSignIcon,
  SteeringWheelIcon,
} from './icons.jsx'

const ROAD_PATH = 'M -80 860 C 160 820, 260 700, 470 720 S 760 860, 980 800 S 1260 560, 1520 600'
const TRUCK_PATH = 'M -80 860 C 160 820, 260 700, 470 720'

const SCATTERED_ICONS = [
  { Icon: FuelPumpIcon, className: 'bg-icon bg-icon--fuel' },
  { Icon: ConeIcon, className: 'bg-icon bg-icon--cone' },
  { Icon: CoffeeIcon, className: 'bg-icon bg-icon--coffee' },
  { Icon: MoonIcon, className: 'bg-icon bg-icon--moon' },
  { Icon: ClockIcon, className: 'bg-icon bg-icon--clock' },
  { Icon: RoadSignIcon, className: 'bg-icon bg-icon--sign' },
  { Icon: SteeringWheelIcon, className: 'bg-icon bg-icon--wheel' },
  { Icon: MapPinIcon, className: 'bg-icon bg-icon--pin' },
]

function prefersReducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

function RoadTruck() {
  return (
    <g transform="translate(-30 -44)" className="road-truck">
      <path d="M5 14h24a1.5 1.5 0 0 1 1.5 1.5V34H3.5V15.5A1.5 1.5 0 0 1 5 14z" />
      <path d="M30.5 21H39l7 7v6H30.5z" />
      <path d="M33 23.5h5l3.5 4H33z" />
      <circle cx="11" cy="36" r="3.6" />
      <circle cx="19" cy="36" r="3.6" />
      <circle cx="40" cy="36" r="3.6" />
    </g>
  )
}

export default function RoadBackground({ showIcons }) {
  const [isStill] = useState(prefersReducedMotion)

  return (
    <div className="road-background" aria-hidden="true">
      <svg className="road-map" viewBox="0 0 1440 900" preserveAspectRatio="xMidYMid slice">
        <g className="contour-lines">
          <path d="M -40 140 C 220 90, 420 190, 680 130 S 1120 60, 1480 120" />
          <path d="M -40 230 C 260 180, 470 290, 720 220 S 1150 150, 1480 210" />
          <path d="M -40 470 C 180 430, 360 520, 600 470 S 1040 400, 1480 460" />
          <path d="M -40 560 C 210 520, 420 610, 640 560 S 1080 490, 1480 550" />
        </g>
        <path className="road-edge" d={ROAD_PATH} />
        <path className="road-surface" d={ROAD_PATH} />
        <path className="road-center-line" d={ROAD_PATH} />
        <path id="truck-route" d={TRUCK_PATH} fill="none" stroke="none" />

        {isStill ? (
          <g transform="translate(470 720)">
            <RoadTruck />
          </g>
        ) : (
          <g>
            <RoadTruck />
            <animateMotion
              dur="6s"
              begin="0s"
              fill="freeze"
              rotate="auto"
              calcMode="spline"
              keyPoints="0;1"
              keyTimes="0;1"
              keySplines="0.35 0 0.2 1"
            >
              <mpath href="#truck-route" />
            </animateMotion>
          </g>
        )}
      </svg>

      {showIcons &&
        SCATTERED_ICONS.map(({ Icon, className }) => <Icon key={className} className={className} />)}
    </div>
  )
}
