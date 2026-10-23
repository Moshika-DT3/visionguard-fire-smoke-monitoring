import { useCallback, useEffect, useState } from 'react'

export interface ApiState<T> {
  /** null until the first successful response; kept during reloads. */
  data: T | null
  error: string | null
  /** Fetch again; keeps showing current data while it loads. */
  reload: () => void
}

/**
 * Run an API loader on mount, with abort on unmount and optional polling.
 * `loader` must be stable (define it at module level or memoize it).
 */
export function useApi<T>(loader: (signal: AbortSignal) => Promise<T>, refreshIntervalMs?: number): ApiState<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    loader(controller.signal)
      .then((result) => {
        setData(result)
        setError(null)
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return
        setError(err instanceof Error ? err.message : 'Something went wrong.')
      })
    return () => controller.abort()
  }, [loader, reloadKey])

  useEffect(() => {
    if (!refreshIntervalMs) return
    const timer = window.setInterval(() => setReloadKey((key) => key + 1), refreshIntervalMs)
    return () => window.clearInterval(timer)
  }, [refreshIntervalMs])

  const reload = useCallback(() => setReloadKey((key) => key + 1), [])

  return { data, error, reload }
}
