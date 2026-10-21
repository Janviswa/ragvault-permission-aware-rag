"use client";

import { useCallback, useSyncExternalStore } from "react";

export type Theme = "light" | "dark";

export const THEME_KEY = "ragvault.theme";

// Runs before first paint (inlined in the root layout) so there is no light flash in dark mode.
export const THEME_INIT_SCRIPT = `(function(){try{var t=localStorage.getItem("${THEME_KEY}");if(t!=="light"&&t!=="dark"){t=window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"}document.documentElement.setAttribute("data-theme",t)}catch(e){}})();`;

const listeners = new Set<() => void>();

function read(): Theme {
  return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
}

function subscribe(callback: () => void) {
  listeners.add(callback);
  return () => {
    listeners.delete(callback);
  };
}

export function useTheme() {
  const theme = useSyncExternalStore(subscribe, read, () => "light" as Theme);

  const setTheme = useCallback((next: Theme) => {
    document.documentElement.setAttribute("data-theme", next);
    try {
      localStorage.setItem(THEME_KEY, next);
    } catch {
      /* storage unavailable: theme still applies for this visit */
    }
    listeners.forEach((listener) => listener());
  }, []);

  const toggle = useCallback(() => setTheme(read() === "dark" ? "light" : "dark"), [setTheme]);

  return { theme, setTheme, toggle };
}
