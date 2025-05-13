# Freya UI - Cyberpunk Hologram Cockpit

A single-screen, no-scroll hologram cockpit interface for the Freya AI companion, built with React 18, Next.js 14 (App Router), Tailwind CSS, and Framer Motion.

## Setup Instructions

### 1. Legacy JavaScript Integration

Copy your legacy JavaScript files to the public directory:

\`\`\`bash
mkdir -p public/legacy
cp -r /path/to/your/js/legacy/* public/legacy/
\`\`\`

The legacy script is already configured to load in `app/layout.tsx` using:

\`\`\`tsx
<Script src="/legacy/main.js" strategy="beforeInteractive" />
\`\`\`

### 2. Video Assets

Place your visualization videos in the public directory:

\`\`\`bash
mkdir -p public/video
cp /path/to/idle.webm public/video/
cp /path/to/reply.webm public/video/
\`\`\`

The application will automatically switch between these videos based on Freya's state.

### 3. Running the Application

Install dependencies and start the development server:

\`\`\`bash
npm install
npm run dev
\`\`\`

The application will be available at [http://localhost:3000](http://localhost:3000).

## Architecture Overview

### Design Philosophy

The Freya UI is designed as a minimalist, cyberpunk-inspired hologram cockpit that provides a clean, immersive interface for interacting with the Freya AI. Key design principles include:

- **Single-screen experience**: No scrolling, everything contained in one view
- **Minimalist aesthetics**: Clean lines, subtle animations, and focused interactions
- **Cyberpunk HUD**: Inspired by sci-fi interfaces with holographic elements
- **Focus on conversation**: Prioritizing the AI interaction over UI elements

### Component Structure

The application is organized into several key components:

1. **Visualizer (`components/Visualizer.tsx`)**: 
   - Displays the central visualization (video or placeholder)
   - Renders HUD rings and animations
   - Changes appearance based on Freya's state (idle/replying)

2. **MessagePair (`components/MessagePair.tsx`)**:
   - Handles the display and animation of user and Freya messages
   - Uses Framer Motion for floating animations
   - Supports long messages with proper text wrapping

3. **InvisibleInput (`components/InvisibleInput.tsx`)**:
   - Provides an invisible text input that stays focused
   - Shows only a blinking cursor when empty
   - Handles form submission and focus management

4. **useFreya Hook (`hooks/useFreya.ts`)**:
   - Bridges React with the legacy JavaScript backend
   - Manages state (idle/listening/replying)
   - Handles message sending and receiving

5. **Main Page (`app/page.tsx`)**:
   - Composes all components into the final layout
   - Manages the message pairs state
   - Handles the overall page structure

## Integration with Legacy Backend

### Communication Flow

The frontend communicates with your legacy backend through the `useFreya` hook, which:

1. Calls `window.sendMessageToAPI(userText)` when a message is sent
2. Listens for custom events from the legacy system:
   - `freya:reply` - When Freya sends a response
   - `freya:listening` - When Freya is listening
   - `freya:thinking` - When Freya is processing (replying)

### Expected Backend Events

Your legacy backend should dispatch these custom events:

\`\`\`javascript
// When Freya starts listening
const listeningEvent = new CustomEvent('freya:listening');
window.dispatchEvent(listeningEvent);

// When Freya is processing a response
const thinkingEvent = new CustomEvent('freya:thinking');
window.dispatchEvent(thinkingEvent);

// When Freya sends a response
const replyEvent = new CustomEvent('freya:reply', {
  detail: { message: "Your response text here" }
});
window.dispatchEvent(replyEvent);
\`\`\`

### Video Source Management

The Visualizer component expects two video sources:
- `/video/idle.webm` - Displayed when Freya is in idle state
- `/video/reply.webm` - Displayed when Freya is processing/replying

The component will automatically switch between these based on Freya's state.

## Floating Messages System

### Message Animation Flow

The floating message system works through a combination of state management and Framer Motion animations:

1. When a user sends a message:
   - The message is stored in state
   - The message animates upward from the input area
   - The state changes to "replying"

2. When Freya responds:
   - The response is stored in state
   - The response animates in below the user message
   - Both messages remain visible until a new message is sent

3. Message positioning:
   - Messages are centered horizontally
   - They use `max-width: 100%` and `break-words` to handle long content
   - The gap between user and Freya messages is controlled via the `gap-6` class

### Animation Implementation

The animations are implemented using Framer Motion:

\`\`\`tsx
// User message animation
<motion.div
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

// Freya response animation
<motion.div
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
\`\`\`

## Invisible Input System

The invisible input system provides a clean interface with just a blinking cursor:

1. **Focus Management**:
   - Uses multiple strategies to maintain focus (interval checks, event listeners)
   - Automatically refocuses after sending messages
   - Handles blur events by refocusing

2. **Visual Feedback**:
   - Shows only a blinking cursor when empty
   - No visible borders or backgrounds
   - Cursor color matches the cyberpunk theme (accent-cy)

3. **Mobile Optimization**:
   - Uses `inputMode="text"` for better mobile keyboard
   - Uses `enterKeyHint="send"` to show the send button on mobile keyboards

## Styling System

### Color Palette

The UI uses a cyberpunk-inspired color palette:

- Background: Gradient from `#0A0F1F` to `#130726`
- Accent Cyan: `#23C6FF` (user messages, HUD elements)
- Accent Magenta: `#A400FF` (Freya messages)
- Glass Foreground: `rgba(255, 255, 255, 0.12)` (subtle highlights)

### Animation Principles

Animations follow these principles:

1. **Subtle and continuous**: HUD rings pulse gently to create a living interface
2. **Purposeful**: Animations convey state changes (idle vs. replying)
3. **Spring physics**: Message animations use spring physics for natural movement
4. **Minimal**: Animations enhance rather than distract from the experience

## Responsive Design

The interface is designed to work well on all screen sizes:

- Uses `max-w-[360px]` for the main content area
- Centers content both horizontally and vertically
- Uses relative sizing for HUD elements
- Adapts input handling for mobile devices

## File Structure

\`\`\`
freya-ui/
├── app/
│   ├── globals.css       # Global styles and CSS variables
│   ├── layout.tsx        # Root layout with Script import
│   └── page.tsx          # Main page composition
├── components/
│   ├── InvisibleInput.tsx # Invisible input with cursor
│   ├── MessagePair.tsx   # Message pair with animations
│   └── Visualizer.tsx    # Central visualization with HUD
├── hooks/
│   └── useFreya.ts       # Hook for backend integration
├── public/
│   ├── legacy/           # Legacy JS files (you provide)
│   └── video/            # Video assets (you provide)
├── tailwind.config.js    # Tailwind configuration
└── README.md             # This documentation
\`\`\`

## Advanced Customization

### Changing the Status Text

The status text ("FREYA // STANDBY", etc.) is generated in the `useFreya` hook:

\`\`\`typescript
const statusText =
  state === "replying" 
    ? "FREYA // REPLYING" 
    : state === "listening" 
      ? "FREYA // LISTENING" 
      : "FREYA // STANDBY";
\`\`\`

### Modifying Animations

Animation timings and properties can be adjusted in the respective components:

- HUD animations in `Visualizer.tsx`
- Message animations in `MessagePair.tsx`
- Cursor blinking in `InvisibleInput.tsx`

### Adding New States

To add new states beyond idle/listening/replying:

1. Update the state type in `useFreya.ts`
2. Add new event listeners for the state
3. Update the statusText computation
4. Add conditional styling in the Visualizer component

## Troubleshooting

### Video Not Playing

If videos don't play:
- Check that video files are in `/public/video/`
- Ensure video format is supported by the browser (WebM or MP4)
- Check browser console for errors

### Messages Not Appearing

If messages don't appear:
- Check that the legacy backend is dispatching the correct events
- Verify the event detail structure matches what the hook expects
- Check browser console for errors

### Input Not Focused

If the input loses focus:
- Check if any other elements might be stealing focus
- Verify that no errors are occurring in the focus management code
- Try clicking on the screen to re-establish focus

## Performance Considerations

The UI is optimized for performance:

- Uses CSS for animations where possible
- Limits the number of animated elements
- Uses efficient Framer Motion animations with hardware acceleration
- Maintains a single source of truth for state
