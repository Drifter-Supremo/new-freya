"use client"

import { useState, useEffect } from "react"
import Visualizer from "@/components/Visualizer"
import MessagePair from "@/components/MessagePair"
import InvisibleInput from "@/components/InvisibleInput"
import { useFreya } from "@/hooks/useFreya"

export default function Home() {
  const { state, statusText, sendMessage, lastUser, lastFreya } = useFreya()
  const [messagePairs, setMessagePairs] = useState<Array<{ id: number; user: string; freya: string }>>([])

  // Load message pairs from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('freya-message-pairs')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        setMessagePairs(parsed)
      } catch (error) {
        console.log('Failed to load saved messages')
      }
    }
  }, [])

  // Save message pairs to localStorage whenever they change
  useEffect(() => {
    if (messagePairs.length > 0) {
      localStorage.setItem('freya-message-pairs', JSON.stringify(messagePairs))
    }
  }, [messagePairs])

  const handleSendMessage = (message: string) => {
    // Create a new message pair with the current message
    const newPair = {
      id: Date.now(),
      user: message,
      freya: "",
    }

    // Update message pairs (keep only the latest)
    setMessagePairs([newPair])

    // Send message to Freya
    sendMessage(message)
  }

  // Update the latest message pair when Freya responds - FIXED VERSION
  useEffect(() => {
    if (lastFreya && messagePairs.length > 0) {
      setMessagePairs(prev => {
        const updated = [...prev]
        // Only update if the current pair doesn't have Freya's response yet, OR if it's a new response
        if (updated[0] && (!updated[0].freya || updated[0].freya !== lastFreya)) {
          updated[0].freya = lastFreya
        }
        return updated
      })
    }
  }, [lastFreya])

  return (
    <main className="h-screen w-full bg-gradient-to-br from-[#0A0F1F] via-[#0D1021] to-[#130726] flex flex-col items-center justify-center overflow-hidden">
      <div className="relative w-full h-full flex flex-col items-center">
        {/* Visualizer - Moved higher on the screen */}
        <div className="flex-1 flex items-center justify-center pt-12 pb-4">
          <Visualizer state={state} />
        </div>

        {/* Status Text */}
        <div className="text-xs tracking-[0.25em] text-accent-cy uppercase font-mono mb-4">{statusText}</div>

        {/* Message Container - More space for longer messages */}
        <div className="w-full max-w-[360px] flex-1 flex flex-col items-center justify-start overflow-hidden px-4 mb-20">
          {messagePairs.map((pair) => (
            <MessagePair key={pair.id} user={pair.user} freya={pair.freya} />
          ))}
        </div>

        {/* Invisible Input - Fixed at bottom */}
        <div className="absolute bottom-8 w-full max-w-[360px] px-4">
          <InvisibleInput onSend={handleSendMessage} disabled={state === "replying"} />
        </div>
      </div>
    </main>
  )
}
