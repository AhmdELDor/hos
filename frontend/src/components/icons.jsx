function LineIcon({ className, children }) {
  return (
    <svg
      className={className}
      viewBox="0 0 48 48"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {children}
    </svg>
  )
}

export function TruckIcon({ className }) {
  return (
    <LineIcon className={className}>
      <path d="M5 14h22a1.5 1.5 0 0 1 1.5 1.5V32H3.5V15.5A1.5 1.5 0 0 1 5 14z" />
      <path d="M28.5 20H36l6.5 6.6V32h-14" />
      <path d="M31 22.5h4l3.3 3.5H31z" />
      <circle cx="11" cy="34" r="3.4" />
      <circle cx="19" cy="34" r="3.4" />
      <circle cx="37" cy="34" r="3.4" />
      <path d="M2 40.5c9-.8 18 .7 27-.3s12 .6 17 0" />
    </LineIcon>
  )
}

export function BoxIcon({ className }) {
  return (
    <LineIcon className={className}>
      <path d="M8 16.5 24 8.5l16 8v17l-16 8-16-8z" />
      <path d="m8 16.5 16 8 16-8" />
      <path d="M24 24.5v17" />
      <path d="m16 12.5 16 8" />
    </LineIcon>
  )
}

export function FlagIcon({ className }) {
  return (
    <LineIcon className={className}>
      <path d="M12 42.5V7" />
      <path d="M12 9c5-3.5 9 1.5 14-.5s7-2 10.5-.5v14c-3.5-1.5-6-1.2-10.5.6S17 21 12 24" />
    </LineIcon>
  )
}

export function FuelPumpIcon({ className }) {
  return (
    <LineIcon className={className}>
      <rect x="9.5" y="8" width="18" height="32" rx="2.5" />
      <rect x="13.5" y="12" width="10" height="8" rx="1.2" />
      <path d="M6.5 40.5h24" />
      <path d="M27.5 17h3.5a3 3 0 0 1 3 3v11.5a2.5 2.5 0 0 0 5 0V18.5L35 14" />
    </LineIcon>
  )
}

export function ClockIcon({ className }) {
  return (
    <LineIcon className={className}>
      <circle cx="24" cy="24" r="15.5" />
      <path d="M24 14.5v10l6.5 4" />
    </LineIcon>
  )
}

export function SteeringWheelIcon({ className }) {
  return (
    <LineIcon className={className}>
      <circle cx="24" cy="24" r="16" />
      <circle cx="24" cy="24" r="4.5" />
      <path d="M8.5 21.5c5-.6 8.5 0 11 1.2" />
      <path d="M39.5 21.5c-5-.6-8.5 0-11 1.2" />
      <path d="M24 28.5v11" />
    </LineIcon>
  )
}

export function ConeIcon({ className }) {
  return (
    <LineIcon className={className}>
      <path d="M17.5 38.5 22.8 10h2.4l5.3 28.5" />
      <path d="M13 38.5h22" />
      <path d="M19.4 29.5h9.2" />
      <path d="M21 21h6" />
    </LineIcon>
  )
}

export function RoadSignIcon({ className }) {
  return (
    <LineIcon className={className}>
      <path d="M24 5.5 42.5 24 24 42.5 5.5 24z" />
      <path d="M19.5 31v-5.5a4.5 4.5 0 0 1 4.5-4.5h6" />
      <path d="m27 17.5 3.5 3.5-3.5 3.5" />
    </LineIcon>
  )
}

export function CoffeeIcon({ className }) {
  return (
    <LineIcon className={className}>
      <path d="M11 19h21v10.5a8.5 8.5 0 0 1-8.5 8.5h-4a8.5 8.5 0 0 1-8.5-8.5z" />
      <path d="M32 22h3a4 4 0 0 1 0 8h-3" />
      <path d="M17.5 8c-2 2.5-2 4.5 0 7" />
      <path d="M24 8c-2 2.5-2 4.5 0 7" />
    </LineIcon>
  )
}

export function MoonIcon({ className }) {
  return (
    <LineIcon className={className}>
      <path d="M29 8.5A15.5 15.5 0 1 0 40 31a12.5 12.5 0 0 1-11-22.5z" />
      <path d="M36 9.5v4M34 11.5h4" />
    </LineIcon>
  )
}

export function MapPinIcon({ className }) {
  return (
    <LineIcon className={className}>
      <path d="M24 42.5S11.5 30.5 11.5 20a12.5 12.5 0 0 1 25 0c0 10.5-12.5 22.5-12.5 22.5z" />
      <circle cx="24" cy="20" r="4.5" />
    </LineIcon>
  )
}
