export default function SiteHeader({ children }) {
  return (
    <header className="site-header">
      <span className="brand">
        <img className="brand__logo" src="/logo.png" alt="HOS" />
        <span className="brand__name">Trip Planner</span>
      </span>
      {children}
    </header>
  )
}
