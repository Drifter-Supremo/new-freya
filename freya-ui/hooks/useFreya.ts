"use client"

import { useState, useEffect } from "react"

declare global {
  interface Window {
    sendMessageToAPI: (userText: string, showStatus?: boolean) => void
  }
}

export function useFreya() {
  const [state, setState] = useState<"idle" | "listening" | "replying">("idle")
  const [lastUser, setLastUser] = useState("")
  const [lastFreya, setLastFreya] = useState("")

  // Compute status text based on state
  const statusText =
    state === "replying" ? "FREYA // REPLYING" : state === "listening" ? "FREYA // LISTENING" : "FREYA // STANDBY"

  // Setup event listeners for the legacy system
  useEffect(() => {
    // This would be implemented by the legacy system
    const handleFreyaReply = (event: CustomEvent) => {
      setLastFreya(event.detail.message)
      setState("idle")
    }

    // Listen for custom events from the legacy system
    window.addEventListener("freya:reply", handleFreyaReply as EventListener)
    window.addEventListener("freya:listening", () => setState("listening"))
    window.addEventListener("freya:thinking", () => setState("replying"))

    return () => {
      window.removeEventListener("freya:reply", handleFreyaReply as EventListener)
      window.removeEventListener("freya:listening", () => setState("listening") as EventListener)
      window.removeEventListener("freya:thinking", () => setState("replying") as EventListener)
    }
  }, [])

  const sendMessage = (userText: string) => {
    setLastUser(userText)
    setState("replying")

    // Call the legacy API function if it exists
    if (typeof window !== "undefined" && window.sendMessageToAPI) {
      window.sendMessageToAPI(userText, false)
    } else {
      console.log("Legacy API not available, simulating response")
      // Simulate a response for development
      setTimeout(() => {
        setLastFreya(`I received your message: "${userText}"`)
        setState("idle")
      }, 1500)
    }
  }

  return {
    state,
    statusText,
    lastUser,
    lastFreya,
    sendMessage,
  }
}
