"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { getApiBaseUrl } from "@/lib/api";

type LivePoint = {
  ts: string;
  requests_per_second: number;
  success_rate: number;
};

export function LiveChart() {
  const [points, setPoints] = useState<LivePoint[]>([]);
  const [disconnected, setDisconnected] = useState(false);
  const retryRef = useRef(0);

  useEffect(() => {
    let source: EventSource | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;

    const connect = () => {
      source = new EventSource(`${getApiBaseUrl()}/dashboard/live`);
      source.onopen = () => {
        retryRef.current = 0;
        setDisconnected(false);
      };
      source.onmessage = (event) => {
        const payload = JSON.parse(event.data) as {
          requests_per_second: number;
          success_rate: number;
        };
        setPoints((prev) => {
          const next = [
            ...prev,
            {
              ts: new Date().toLocaleTimeString(),
              requests_per_second: payload.requests_per_second,
              success_rate: payload.success_rate,
            },
          ];
          return next.slice(-30);
        });
      };
      source.onerror = () => {
        source?.close();
        setDisconnected(true);
        const delay = Math.min(30_000, 1000 * 2 ** retryRef.current);
        retryRef.current += 1;
        retryTimer = setTimeout(connect, delay);
      };
    };

    connect();
    return () => {
      source?.close();
      if (retryTimer) clearTimeout(retryTimer);
    };
  }, []);

  const hasData = useMemo(() => points.length > 0, [points.length]);

  if (!hasData) {
    return (
      <p className="text-sm text-slate-400">
        {disconnected
          ? "Reconnecting to live metrics…"
          : "Waiting for live gateway traffic…"}
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {disconnected ? (
        <p className="text-xs text-amber-400">Live stream reconnecting…</p>
      ) : null}
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={points}>
            <CartesianGrid stroke="#334155" strokeDasharray="3 3" />
            <XAxis dataKey="ts" stroke="#94a3b8" hide />
            <YAxis stroke="#94a3b8" />
            <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155" }} />
            <Line type="monotone" dataKey="requests_per_second" stroke="#38bdf8" dot={false} />
            <Line type="monotone" dataKey="success_rate" stroke="#34d399" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}