"use client"

import { motion, AnimatePresence } from "framer-motion"

interface MessagePairProps {
  user: string
  freya: string
}

export default function MessagePair({ user, freya }: MessagePairProps) {
  return (
    <div className="w-full flex flex-col items-center gap-6 mb-2">
      {/* User message - Now with text wrapping for longer messages */}
      <motion.div
        className="text-accent-cy text-sm text-center max-w-[100%] break-words"
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{
          type: "spring",
          stiffness: 300,
          damping: 30,
        }}
      >
        {user}
      </motion.div>

      {/* Freya response - Now with text wrapping for longer messages */}
      <AnimatePresence>
        {freya && (
          <motion.div
            className="text-accent-mag text-sm text-center max-w-[100%] break-words"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{
              type: "spring",
              stiffness: 300,
              damping: 30,
              delay: 0.2,
            }}
          >
            {freya}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
