"use client";

import { DependencyList, useCallback, useEffect, useRef, useState } from "react";
import { useSession } from "./session";

/** Load data on mount (and when deps change). 401s are handled by the session. */
export function useLoad<T>(loader: () => Promise<T>, deps: DependencyList = []) {
  const { handleError } = useSession();
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const loaderRef = useRef(loader);
  loaderRef.current = loader;

  const reload = useCallback(async () => {
    try {
      setData(await loaderRef.current());
      setError("");
    } catch (cause) {
      setError(handleError(cause));
    } finally {
      setLoading(false);
    }
  }, [handleError]);

  useEffect(() => {
    setLoading(true);
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reload, ...deps]);

  return { data, setData, error, loading, reload };
}

/** Run an async action with busy/error state. Returns true when it succeeded. */
export function useAction() {
  const { handleError } = useSession();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const run = useCallback(
    async (action: () => Promise<string | void>): Promise<boolean> => {
      setBusy(true);
      setError("");
      setNotice("");
      try {
        const message = await action();
        if (typeof message === "string") setNotice(message);
        return true;
      } catch (cause) {
        setError(handleError(cause));
        return false;
      } finally {
        setBusy(false);
      }
    },
    [handleError],
  );

  const clear = useCallback(() => {
    setError("");
    setNotice("");
  }, []);

  return { busy, error, notice, run, clear };
}
