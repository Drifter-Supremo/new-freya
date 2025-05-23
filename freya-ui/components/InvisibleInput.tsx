"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import { motion } from "framer-motion"

interface InvisibleInputProps {
  onSend: (message: string) => void
  disabled?: boolean
}

export default function InvisibleInput({ onSend, disabled = false }: InvisibleInputProps) {
  const [message, setMessage] = useState("")
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const [isFocused, setIsFocused] = useState(true)

  // Focus management
  useEffect(() => {
    // Initial focus
    if (inputRef.current) {
      inputRef.current.focus()
    }

    // Function to ensure input is focused
    const ensureFocus = () => {
      if (inputRef.current && document.activeElement !== inputRef.current) {
        inputRef.current.focus()
      }
    }

    // Set up multiple ways to maintain focus
    const interval = setInterval(ensureFocus, 300) // Periodically check focus
    window.addEventListener("click", ensureFocus)
    window.addEventListener("focus", ensureFocus)
    document.addEventListener("visibilitychange", ensureFocus)

    return () => {
      clearInterval(interval)
      window.removeEventListener("click", ensureFocus)
      window.removeEventListener("focus", ensureFocus)
      document.removeEventListener("visibilitychange", ensureFocus)
    }
  }, [])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (message.trim() && !disabled) {
      onSend(message.trim())
      setMessage("")

      // Force focus after submission with multiple attempts
      setTimeout(() => {
        if (inputRef.current) inputRef.current.focus()
      }, 0)

      setTimeout(() => {
        if (inputRef.current) inputRef.current.focus()
      }, 50)

      setTimeout(() => {
        if (inputRef.current) inputRef.current.focus()
      }, 150)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = "auto"
      inputRef.current.style.height = `${inputRef.current.scrollHeight}px`
    }
  }, [message])

  return (
    <div className="w-full min-h-12 flex items-center justify-center cursor-text">
      <form onSubmit={handleSubmit} className="w-full relative flex items-center justify-center">
        {/* Completely invisible textarea - no border, no background */}
        <textarea
          ref={inputRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          className={`w-full bg-transparent border-0 outline-none text-white/80 text-center resize-none leading-relaxed ${message === "" ? "caret-transparent" : "caret-accent-cy"}`}
          disabled={disabled}
          onFocus={() => setIsFocused(true)}
          onBlur={() => {
            setIsFocused(false)
            // Refocus when blurred
            setTimeout(() => {
              if (inputRef.current) inputRef.current.focus()
            }, 10)
          }}
          aria-label="Message input"
          autoFocus
          rows={1}
          style={{ 
            minHeight: "1.5rem",
            maxHeight: "8rem",
            overflow: message.length > 100 ? "auto" : "hidden"
          }}
        />

        {/* Blinking cursor when empty and focused */}
        {message === "" && isFocused && (
          <motion.div
            className="absolute h-4 w-[1px] bg-accent-cy"
            animate={{ opacity: [1, 0, 1] }}
            transition={{ repeat: Number.POSITIVE_INFINITY, duration: 1 }}
          />
        )}
      </form>
    </div>
  )
}
