import { Toaster as Sonner } from "sonner"

export function Toaster() {
  return (
    <Sonner
      theme="system"
      className="toaster group"
      toastOptions={{
        classNames: {
          toast: "glass-panel border-border text-foreground",
        },
      }}
    />
  )
}
