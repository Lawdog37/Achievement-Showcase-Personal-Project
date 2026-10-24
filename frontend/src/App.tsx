import { Link, Route, Routes } from 'react-router'
import HuntingPage from './pages/HuntingPage'
import NearCompletionPage from './pages/NearCompletionPage'
import OverviewPage from './pages/OverviewPage'
import PlayerLayout from './pages/PlayerLayout'
import ProfilePage from './pages/ProfilePage'

export default function App() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-800">
        <div className="mx-auto max-w-6xl px-4 py-4">
          <Link to="/" className="text-lg font-semibold tracking-tight">
            Achievement Showcase
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">
        <Routes>
          <Route path="/" element={<OverviewPage />} />
          {/* Nested routes: PlayerLayout shows the header and tabs, and its
              <Outlet /> shows the child page that matches the rest of the URL */}
          <Route path="/player/:steamId" element={<PlayerLayout />}>
            <Route index element={<ProfilePage />} />
            <Route path="near-completion" element={<NearCompletionPage />} />
            <Route path="hunting" element={<HuntingPage />} />
          </Route>
          <Route path="*" element={<p className="text-slate-400">Page not found.</p>} />
        </Routes>
      </main>
      <footer className="mx-auto max-w-6xl px-4 py-8 text-xs text-slate-500">
        {/* Steam's API terms ask apps to credit Steam like this */}
        <a href="https://store.steampowered.com" className="hover:text-slate-300">
          Powered by Steam
        </a>
        . Not affiliated with Valve.
      </footer>
    </div>
  )
}
