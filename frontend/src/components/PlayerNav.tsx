import { NavLink } from 'react-router'

// Tabs under the player header. NavLink knows when its page is the one showing.
const TABS = [
  { to: '', label: 'Profile' },
  { to: 'near-completion', label: 'Near completion' },
]

export function PlayerNav() {
  return (
    <nav className="mt-6 flex gap-1 overflow-x-auto overflow-y-hidden border-b border-slate-800">
      {TABS.map((tab) => (
        <NavLink
          key={tab.label}
          to={tab.to}
          end // "Profile" is only active on the exact profile URL
          className={({ isActive }) =>
            `-mb-px shrink-0 border-b-2 px-4 py-2 text-sm font-medium ${
              isActive
                ? 'border-sky-400 text-slate-100'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`
          }
        >
          {tab.label}
        </NavLink>
      ))}
      <span
        className="shrink-0 cursor-not-allowed px-4 py-2 text-sm text-slate-600"
        title="Coming in the next phase"
      >
        Hunting (soon)
      </span>
    </nav>
  )
}
