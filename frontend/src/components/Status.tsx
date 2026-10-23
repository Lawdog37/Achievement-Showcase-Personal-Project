// Small shared pieces for "loading" and "something went wrong".
import type { ReactNode } from 'react'

export function LoadingBlock({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 py-8 text-slate-400" role="status">
      <span className="size-4 animate-spin rounded-full border-2 border-slate-600 border-t-sky-400" />
      {label}
    </div>
  )
}

export function ErrorBlock({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-rose-500/40 bg-rose-500/10 p-4 text-rose-300" role="alert">
      {message}
    </div>
  )
}

export function Section({
  title,
  subtitle,
  children,
}: {
  title: string
  subtitle?: string
  children: ReactNode
}) {
  return (
    <section className="mt-10">
      <h2 className="text-xl font-semibold">{title}</h2>
      {subtitle && <p className="mt-1 text-sm text-slate-400">{subtitle}</p>}
      <div className="mt-4">{children}</div>
    </section>
  )
}