import { Link, Route, Routes } from 'react-router'
import HomePage from './pages/HomePage'
import NearCompletionPage from './pages/NearCompletionPage'
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
          <Route path="/" element={<HomePage />} />
          {/* Nested routes: PlayerLayout shows the header and tabs, and its
              <Outlet /> shows the child page that matches the rest of the URL */}
          <Route path="/player/:steamId" element={<PlayerLayout />}>
            <Route index element={<ProfilePage />} />
            <Route path="near-completion" element={<NearCompletionPage />} />
          </Route>
          <Route path="*" element={<p className="text-slate-400">Page not found.</p>} />
        </Routes>
      </main>
    </div>
  )
}
