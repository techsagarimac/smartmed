import { useEffect, useState } from "react";
import { api } from "../services/api";

export function useReminders(enabled) {
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!enabled) return undefined;
    let cancelled = false;

    async function load() {
      try {
        const data = await api.reminders();
        if (!cancelled) {
          setItems(data);
          setError("");
        }
      } catch (err) {
        if (!cancelled) setError(err.message);
      }
    }

    load();
    const timer = window.setInterval(load, 30000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [enabled]);

  const due = items.filter((item) => item.status === "due" || item.status === "overdue");
  return { items, due, error };
}
