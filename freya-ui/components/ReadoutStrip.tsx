"use client"

import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"

interface ReadoutStripProps {
  lastUser: string
  lastFreya: string
}

interface MessagePair {
  id: number
  user: string
  freya: string
}

export default function ReadoutStrip({ lastUser, lastFreya }: ReadoutStripProps) {
  const [messages, setMessages] = useState<MessagePair[]>([])

  useEffect(() => {
    // Only add a new message pair if both lastUser and lastFreya have values
    if (lastUser || lastFreya) {
      const newPair = {
        id: Date.now(),
        user: lastUser || "hello",
        freya: lastFreya || "hi",
      }

      setMessages((prev) => {
        // Keep only the most recent message
        return [newPair]
      })

      // Remove old messages after 6 seconds
      const timer = setTimeout(() => {
        setMessages((prev) => prev.filter((msg) => msg.id !== newPair.id))
      }, 6000)

      return () => clearTimeout(timer)
    }
  }, [lastUser, lastFreya])

  return (
    <div className="w-full h-16 bg-black/20 backdrop-blur-sm rounded-lg border border-glass-fg mb-6 overflow-hidden">
      <AnimatePresence>
        {messages.map((pair) => (
          <motion.div
            key={pair.id}
            className="grid grid-cols-2 h-full"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -20, opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="flex items-center px-3 border-r border-glass-fg">
              <p className="text-sm text-white/80 truncate">
                <span className="text-accent-cy font-medium">User › </span>
                {pair.user}
              </p>
            </div>
            <div className="flex items-center px-3">
              <p className="text-sm text-white/80 truncate">
                <span className="text-accent-mag font-medium">Freya › </span>
                {pair.freya}
              </p>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}
