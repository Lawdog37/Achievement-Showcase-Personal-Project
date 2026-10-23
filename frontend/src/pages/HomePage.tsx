import { useMutation } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router'
import { api } from '../api/client'

export default function HomePage() {
  const [input, setInput] = useState('')
  const navigate = useNavigate()
  const resolve = useMutation({
    mutationFn: api.resolve,
    onSuccess: ({ steam_id }) => navigate(`/player/${steam_id}`),
  })

  function handleSubmit(event: FormEvent) {
    event.preventDefault() // stop the browser reloading the page
    if (input.trim()) resolve.mutate(input.trim())
  }

  return (
    <div className="mx-auto max-w-xl py-16 text-center">
      <h1 className="text-4xl font-bold tracking-tight">Show off your rarest achievements</h1>
      <p className="mt-3 text-slate-400">
        Enter a Steam profile URL, custom name or SteamID. The profile's game details must be public.
      </p>
      <form onSubmit={handleSubmit} className="mt-8 flex gap-2">
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="steamcommunity.com/id/yourname"
          aria-label="Steam profile"
          className="min-w-0 flex-1 rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 outline-none focus:border-sky-400"
        />
        <button
          type="submit"
          disabled={resolve.isPending}
          className="rounded-lg bg-sky-500 px-5 py-2 font-medium text-slate-950 hover:bg-sky-400 disabled:opacity-60"
        >
          {resolve.isPending ? 'Looking up…' : 'Go'}
        </button>
      </form>
      {resolve.error && <p className="mt-3 text-sm text-rose-400">{resolve.error.message}</p>}
    </div>
  )
}