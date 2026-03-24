import { useEffect, useRef, useState } from "react";

interface VideoFeedProps {
  /** Frame como string base64 (data URI o solo el base64 puro) */
  frame: string | null;
  /** Etiqueta opcional para el label de la cámara */
  label?: string;
  /** Ubicación de la cámara */
  location?: string;
  /** Controles de cámara extra (slot para botones) */
  children?: React.ReactNode;
  /** Si es una card grande o compacta */
  large?: boolean;
}

const NO_SIGNAL_TIMEOUT_MS = 5_000;

export default function VideoFeed({
  frame,
  label = "Cámara 1",
  location = "Anaquel principal",
  large = false,
  children,
}: VideoFeedProps) {
  const [hasSignal, setHasSignal] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastFrameRef = useRef<string | null>(null);

  useEffect(() => {
    if (frame && frame !== lastFrameRef.current) {
      lastFrameRef.current = frame;
      setHasSignal(true);

      // Reiniciar timeout cada vez que llega un frame
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => {
        setHasSignal(false);
      }, NO_SIGNAL_TIMEOUT_MS);
    }

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [frame]);

  const frameSrc = frame
    ? frame.startsWith("data:") ? frame : `data:image/jpeg;base64,${frame}`
    : null;

  return (
    <div className={`bento-card overflow-hidden ${large ? "min-h-[420px]" : "min-h-[260px]"} animate-slide-in flex flex-col`}>
      {/* Header */}
      <div className="px-card-pad pt-3 pb-2 flex items-center justify-between border-b border-gray-100">
        <div className="flex items-center gap-2">
          <span className={`connection-dot ${hasSignal ? "connection-dot-online" : "connection-dot-offline"}`} />
          <h3 className="card-heading">{label}</h3>
          <span className="section-label normal-case">— {location}</span>
        </div>
        {hasSignal ? (
          <div className="live-badge">
            <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse-live" />
            EN VIVO
          </div>
        ) : (
          <div className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-gray-200 text-[10px] font-bold text-gray-500 uppercase tracking-wider">
            <span className="w-1.5 h-1.5 rounded-full bg-gray-400" />
            SIN SEÑAL
          </div>
        )}
      </div>

      {/* Video area */}
      <div className="flex-1 relative bg-gradient-to-b from-gray-50 to-gray-100/50">
        {hasSignal && frameSrc ? (
          <img
            src={frameSrc}
            alt={`Feed de ${label}`}
            className="w-full h-full object-contain"
          />
        ) : (
          <div className="flex-1 flex items-center justify-center p-8 h-full">
            <div className="text-center">
              <div className="w-16 h-16 rounded-3xl bg-gray-200/80 flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl text-gray-400">📷</span>
              </div>
              <p className="text-dense-sm font-medium text-gray-400">{label}</p>
              <p className="text-dense-xs text-gray-300 mt-1">
                {hasSignal ? "Esperando stream del backend..." : "Sin señal — verificar conexión con el backend"}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Slot para controles de cámara */}
      {children}
    </div>
  );
}
