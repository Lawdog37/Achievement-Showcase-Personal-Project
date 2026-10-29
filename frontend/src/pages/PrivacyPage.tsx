import { useNavigate } from 'react-router'
import { SignInLink } from '../components/AccountMenu'
import { useDeleteMyData, useMe } from '../hooks/usePlayerData'

function DeleteMyData({ steamId }: { steamId: string }) {
  const navigate = useNavigate()
  const deleteData = useDeleteMyData(steamId)

  function handleClick() {
    // A browser confirm box: simple, and impossible to click by accident
    const sure = window.confirm(
      'Delete your profile, achievements and hunts from this site? You can sync again later to start fresh.',
    )
    if (sure) deleteData.mutate(undefined, { onSuccess: () => navigate('/') })
  }

  return (
    <div className="mt-4 rounded-xl border border-rose-500/30 bg-rose-500/5 p-4">
      <p className="font-medium">Delete my data</p>
      <p className="mt-1 text-sm text-slate-400">
        Removes your profile, unlocked achievements and hunt list, and signs you out.
      </p>
      <button
        type="button"
        onClick={handleClick}
        disabled={deleteData.isPending}
        className="mt-3 rounded-lg border border-rose-500/60 px-3 py-1.5 text-sm text-rose-300 hover:bg-rose-500/10 disabled:opacity-60"
      >
        {deleteData.isPending ? 'Deleting…' : 'Delete my data'}
      </button>
      {deleteData.error && <p className="mt-2 text-sm text-rose-400">{deleteData.error.message}</p>}
    </div>
  )
}

export default function PrivacyPage() {
  const me = useMe()

  return (
    <article className="mx-auto max-w-2xl space-y-4 text-slate-300">
      <h1 className="text-2xl font-bold text-slate-100">Privacy</h1>

      <h2 className="pt-2 font-semibold text-slate-100">What this site stores</h2>
      <ul className="list-disc space-y-1 pl-6">
        <li>
          Your public Steam profile: SteamID, display name and avatar, copied from Steam when you
          sync.
        </li>
        <li>Your games, playtime and unlocked achievements, also copied from Steam.</li>
        <li>The games you choose to hunt.</li>
      </ul>
      <p>
        That's all. This site never sees your Steam password: you sign in on Steam's own page, and
        Steam only tells us your SteamID.
      </p>

      <h2 className="pt-2 font-semibold text-slate-100">Cookies and storage</h2>
      <p>
        One cookie keeps you signed in. Your browser also remembers the last profile you viewed, for
        the "welcome back" card. There are no ads, trackers or analytics.
      </p>

      <h2 className="pt-2 font-semibold text-slate-100">Your choices</h2>
      <p>
        Anyone can view a synced profile, the same as on Steam. To stop sharing, set your Steam
        profile to private and delete your data here.
      </p>

      {me.data ? (
        <DeleteMyData steamId={me.data.steam_id} />
      ) : (
        <p>
          <SignInLink>Sign in through Steam</SignInLink> to delete your data.
        </p>
      )}
    </article>
  )
}
