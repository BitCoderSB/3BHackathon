import { useState } from "react";
import { useSocketContext } from "../hooks/useSocket";

export default function VideoFeedPiP() {
  const [activeCam, setActiveCam] = useState(0);
  const [minimized, setMinimized] = useState(false);
  const { videoFrame, connected, cameras } = useSocketContext();
  const cam = cameras[activeCam] ?? { label: "Cámara", location: "", source_id: "cam-1", status: "offline" as const };
  const hasFrame = !!videoFrame;

  if (minimized) {
    return (
      <button
        onClick={() => setMinimized(false)}
        className="fixed bottom-4 right-4 z-50 w-12 h-12 rounded-2xl bg-brand-red text-white shadow-bento flex items-center justify-center hover:bg-brand-dark hover:scale-105 transition-all"
        title="Mostrar cámara"
      >
        📹
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 w-[280px] rounded-3xl overflow-hidden shadow-bento-hover border border-gray-200/60 bg-black animate-slide-in">
      {/* Placeholder del video */}
      <div className="relative aspect-video bg-gradient-to-b from-gray-800 to-gray-900 flex items-center justify-center overflow-hidden">
        {hasFrame ? (
          <img
            src={videoFrame!.startsWith("data:") ? videoFrame! : `data:image/jpeg;base64,${videoFrame}`}
            alt={`Feed de ${cam.label}`}
            className="w-full h-full object-contain"
          />
        ) : (
          <div className="text-center">
            <span className="text-3xl">📷</span>
            <p className="text-dense-xs text-gray-400 mt-1">{cam.label}</p>
            <p className="text-[9px] text-gray-500">{cam.location}</p>
          </div>
        )}
        {/* Live badge */}
        {hasFrame ? (
          <div className="absolute top-2 left-2 live-badge">
            <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse-live" />
            EN VIVO
          </div>
        ) : (
          <div className="absolute top-2 left-2 flex items-center gap-1.5 px-2 py-1 rounded-lg bg-gray-700/80 text-[10px] font-bold text-gray-400 uppercase tracking-wider">
            <span className="w-1.5 h-1.5 rounded-full bg-gray-500" />
            SIN SEÑAL
          </div>
        )}
        {/* Minimize button */}
        <button
          onClick={() => setMinimized(true)}
          className="absolute top-2 right-2 w-6 h-6 rounded-xl bg-black/40 text-white flex items-center justify-center hover:bg-black/60 transition-colors text-[10px] backdrop-blur-sm"
          title="Minimizar"
        >
          ✕
        </button>
      </div>
      {/* Camera controls — skill: pill-toggle + connection-dot */}
      <div className="bg-white px-3 py-2 flex items-center justify-between">
        <div className="flex gap-1">
          {cameras.map((c, i) => (
            <button
              key={c.source_id}
              onClick={() => setActiveCam(i)}
              className={`pill-toggle ${i === activeCam ? "pill-toggle-active" : "pill-toggle-inactive"}`}
            >
              {c.label}
            </button>
          ))}
        </div>
        <span className={`connection-dot ${connected ? "connection-dot-online" : "connection-dot-offline"}`} />
      </div>
    </div>
  );
}
