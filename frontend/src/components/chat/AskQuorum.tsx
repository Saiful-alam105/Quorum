import { useEffect, useState } from "react"

import { AskQuorumButton } from "@/components/chat/AskQuorumButton"
import { AskQuorumPanel } from "@/components/chat/AskQuorumPanel"

export function AskQuorum() {
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (!open) {
      return
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false)
      }
    }
    document.addEventListener("keydown", onKeyDown)
    return () => document.removeEventListener("keydown", onKeyDown)
  }, [open])

  return (
    <>
      <AskQuorumPanel open={open} onClose={() => setOpen(false)} />
      <AskQuorumButton open={open} onToggle={() => setOpen((value) => !value)} />
    </>
  )
}