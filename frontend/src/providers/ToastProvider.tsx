"use client";

/** §9: global toast for mutation errors (and the odd success note). */

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

export interface Toast {
  id: number;
  message: string;
  tone: "error" | "success";
}

interface ToastContextValue {
  toast: (message: string, tone?: Toast["tone"]) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const nextId = useRef(1);

  const toast = useCallback((message: string, tone: Toast["tone"] = "error") => {
    const id = nextId.current++;
    setToasts((current) => [...current, { id, message, tone }]);
    setTimeout(() => {
      setToasts((current) => current.filter((t) => t.id !== id));
    }, 5000);
  }, []);

  const value = useMemo(() => ({ toast }), [toast]);
  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toast-stack" role="status" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={`toast toast-${t.tone}`}>
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext);
  if (context === null) throw new Error("useToast must be used within ToastProvider");
  return context;
}
