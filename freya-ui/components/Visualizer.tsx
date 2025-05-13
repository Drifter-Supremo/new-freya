"use client"

import { motion } from "framer-motion"

interface VisualizerProps {
  state: "idle" | "listening" | "replying"
}

export default function Visualizer({ state }: VisualizerProps) {
  return (
    <div className="relative w-full max-w-[360px] aspect-video flex items-center justify-center">
      {/* Custom placeholder instead of default white box */}
      <div className="w-full h-full bg-bg-deep/50 flex items-center justify-center">
        {/* Animated placeholder content */}
        <motion.div
          className="relative w-full h-full flex items-center justify-center"
          initial={{ opacity: 0.7 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY, repeatType: "reverse" }}
        >
          {/* Center hexagon */}
          <div className="w-24 h-24 relative">
            <svg viewBox="0 0 100 100" className="w-full h-full">
              <motion.polygon
                points="50,0 93.3,25 93.3,75 50,100 6.7,75 6.7,25"
                fill="transparent"
                stroke="#23C6FF"
                strokeWidth="1"
                initial={{ opacity: 0.5 }}
                animate={{
                  opacity: [0.3, 0.7, 0.3],
                  scale: [1, 1.05, 1],
                }}
                transition={{
                  duration: 3,
                  repeat: Number.POSITIVE_INFINITY,
                  repeatType: "reverse",
                }}
              />
            </svg>

            {/* Inner circle */}
            <motion.div
              className="absolute inset-0 flex items-center justify-center"
              animate={{
                rotate: 360,
              }}
              transition={{
                duration: 20,
                repeat: Number.POSITIVE_INFINITY,
                ease: "linear",
              }}
            >
              <div className="w-12 h-12 rounded-full border border-accent-cy/30 flex items-center justify-center">
                <div className="w-6 h-6 rounded-full bg-accent-cy/10"></div>
              </div>
            </motion.div>
          </div>
        </motion.div>
      </div>

      {/* HUD Rings Overlay */}
      <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
        {/* Outer ring */}
        <motion.div
          className="absolute w-[90%] h-[90%] rounded-full border border-accent-cy/30"
          animate={{
            scale: [1, 1.05, 1],
            opacity: [0.3, 0.5, 0.3],
          }}
          transition={{
            repeat: Number.POSITIVE_INFINITY,
            duration: 4,
            ease: "easeInOut",
          }}
        />

        {/* Middle ring */}
        <motion.div
          className="absolute w-[70%] h-[70%] rounded-full border border-accent-cy/40"
          animate={{
            scale: [1, 1.03, 1],
            opacity: [0.4, 0.6, 0.4],
          }}
          transition={{
            repeat: Number.POSITIVE_INFINITY,
            duration: 3,
            ease: "easeInOut",
            delay: 0.5,
          }}
        />

        {/* Inner ring */}
        <motion.div
          className="absolute w-[50%] h-[50%] rounded-full border border-accent-cy/50"
          animate={{
            scale: [1, 1.08, 1],
            opacity: [0.5, 0.7, 0.5],
          }}
          transition={{
            repeat: Number.POSITIVE_INFINITY,
            duration: 2.5,
            ease: "easeInOut",
            delay: 1,
          }}
        />

        {/* Center dot */}
        <motion.div
          className="absolute w-[5%] h-[5%] rounded-full bg-accent-cy"
          animate={{
            scale: [1, 1.5, 1],
            opacity: [0.7, 1, 0.7],
          }}
          transition={{
            repeat: Number.POSITIVE_INFINITY,
            duration: 2,
            ease: "easeInOut",
          }}
        />
      </div>

      {/* Glow effect when replying */}
      {state === "replying" && (
        <motion.div
          className="absolute inset-0 rounded-full bg-accent-cy/10 blur-xl"
          animate={{
            opacity: [0.1, 0.3, 0.1],
          }}
          transition={{
            repeat: Number.POSITIVE_INFINITY,
            duration: 1.5,
            ease: "easeInOut",
          }}
        />
      )}
    </div>
  )
}
