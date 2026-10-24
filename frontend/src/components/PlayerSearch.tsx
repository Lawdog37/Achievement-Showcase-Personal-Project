import { useMutation } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router'
import { api } from '../api/client'

/** The "enter your Steam profile" box. Moved here from the old HomePage. */
export function PlayerSearch() {
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
    <div>
      <form onSubmit={handleSubmit} className="flex gap-2">
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
