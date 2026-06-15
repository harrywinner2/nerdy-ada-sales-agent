import { useEffect, useState, useCallback, useRef } from 'react'

// Small data-fetching hook. `fn` should be stable or memoized by the caller.
export function useFetch(fn, deps = []) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const mounted = useRef(true)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await fn()
      if (mounted.current) setData(result)
    } catch (e) {
      if (mounted.current) setError(e.message || 'Failed to load')
    } finally {
      if (mounted.current) setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => {
    mounted.current = true
    load()
    return () => {
      mounted.current = false
    }
  }, [load])

  return { data, error, loading, reload: load }
}

export default useFetch
