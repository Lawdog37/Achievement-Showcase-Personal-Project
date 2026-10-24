import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { useLogout, useMe } from '../hooks/usePlayerData'

/**
 * A link that starts "Sign in through Steam". It's a plain <a>, not a router
 * <Link>, because it leaves our app: the backend sends the browser to Steam.
 */
export function SignInLink({ children }: { children: ReactNode }) {
  return (
    <a href="/api/auth/login" className="text-sky-400 hover:underline">
      {children}
    </a>
  )
}

/** Top-right corner: "Sign in through Steam", or "My profile · Sign out". */
export function AccountMenu() {
  const me = useMe()
  const logout = useLogout()

  if (me.isPending) return null // don't flash the wrong button while checking

  if (!me.data) {
    return (
      <a
        href="/api/auth/login"
        className="rounded-lg border border-slate-700 px-3 py-1.5 text-sm hover:border-slate-500"
      >
        Sign in through Steam
      </a>
    )
  }

  return (
    <div className="flex items-center gap-3 text-sm">
      <Link to={`/player/${me.data.steam_id}`} className="text-slate-300 hover:text-white">
        My profile
      </Link>
      <button
        type="button"
        onClick={() => logout.mutate()}
        className="rounded-lg border border-slate-700 px-3 py-1.5 hover:border-slate-500"
      >
        Sign out
      </button>
    </div>
  )
}
