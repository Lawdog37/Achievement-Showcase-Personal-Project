import { Link, Route, Routes } from 'react-router'
import HomePage from './pages/HomePage'
import PlayerPage from './pages/PlayerPage'

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
          <Route path="/player/:steamId" element={<PlayerPage />} />
          <Route path="*" element={<p className="text-slate-400">Page not found.</p>} />
        </Routes>
      </main>
    </div>
  )
}