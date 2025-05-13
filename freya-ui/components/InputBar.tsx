"use client"

import type React from "react"

import { useState } from "react"
import { motion } from "framer-motion"
import { Send } from "lucide-react"

interface InputBarProps {
  onSend: (message: string) => void
  disabled?: boolean
}

export default function InputBar({ onSend, disabled = false }: InputBarProps) {
  const [message, setMessage] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (message.trim() && !disabled) {
      onSend(message.trim())
      setMessage("")
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full relative">
      <div className="relative flex items-center w-full rounded-full bg-black/30 backdrop-blur-md border border-accent-cy/50 overflow-hidden">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Message Freya..."
          className="flex-1 bg-transparent px-4 py-3 text-white focus:outline-none caret-accent-cy placeholder:text-white/50"
          disabled={disabled}
        />

        <motion.button
          type="submit"
          disabled={!message.trim() || disabled}
          className="flex items-center justify-center h-10 w-10 mr-1 rounded-full bg-gradient-to-r from-accent-cy to-accent-mag disabled:opacity-50 disabled:grayscale"
          whileTap={{ scale: 0.9 }}
          transition={{ type: "spring", stiffness: 400, damping: 10, duration: 0.09 }}
        >
          <Send size={18} className="text-white" />
          <div className="absolute inset-0 rounded-full bg-accent-cy/20 blur-sm"></div>
        </motion.button>
      </div>

      {/* Glow effect */}
      <div className="absolute inset-0 -z-10 rounded-full bg-accent-cy/10 blur-md"></div>
    </form>
  )
}
