# GestureOS Controls

## Quick Start

1. Run the application:

```bash
python main.py
```

2. Show your hand to the webcam.
3. Use the gestures below to control your computer.

---

## Modes

GestureOS has three modes. The default mode is **Mouse Mode**.

| Mode | Activation Gesture | Deactivation Gesture |
| ---- | ------------------ | -------------------- |
| Mouse Mode | Default | — |
| Volume Mode | Open hand held 2 seconds | Open hand held 2 seconds |
| Media Mode | Peace sign held 2 seconds | Peace sign held 2 seconds |

---

## Mouse Mode (Default)

| Gesture | Action |
| ------- | ------ |
| Move index finger | Move mouse cursor |
| Thumb + Index pinch | Left click |
| Thumb + Middle pinch | Right click |
| Index + Middle up (index above middle) | Scroll up |
| Index + Middle up (middle above index) | Scroll down |
| Open hand held 2 seconds | Switch to Volume Mode |
| Peace sign held 2 seconds | Switch to Media Mode |

---

## Volume Mode

| Gesture | Action |
| ------- | ------ |
| Adjust thumb–index distance | Set volume level (closer = quieter, farther = louder) |
| Open hand held 2 seconds | Return to Mouse Mode |

---

## Media Mode

| Gesture | Action |
| ------- | ------ |
| Open palm | Play / Pause |
| Swipe right | Next Track |
| Swipe left | Previous Track |
| Peace sign held 2 seconds | Return to Mouse Mode |

---

## Global Controls

| Gesture | Action |
| ------- | ------ |
| Closed fist (hold 2 seconds) | Exit application |
| Three-finger pinch (thumb + index + middle, hold briefly) | Take screenshot |
| Q key | Exit application |

---

## Screenshots

Screenshots are saved automatically to:

```
assets/screenshots/screenshot_YYYYMMDD_HHMMSS.png
```

---

## Current Features

- Real-time hand tracking
- Mouse cursor control
- Left click / Right click
- Scrolling
- Volume control
- Media playback control (play/pause, next, previous)
- Screenshot capture
- Safe exit gesture
- Keyboard exit (Q)

---

## Planned Features

- Presentation Mode
- Gaming Mode
- Custom Gestures
- Gesture Analytics
- AI Gesture Recognition
- User Profiles

---

## Tips

- Use good lighting for better tracking.
- Keep your hand inside the camera frame.
- Use the default 640x480 resolution for best performance.
- Mode switches require holding the activation gesture for 2 full seconds.
- After a mode switch, wait 1.5s before switching again (cooldown).
- Press **Q** if you need to exit quickly.

---

## Troubleshooting

**Cursor feels slow**

- Reduce cursor smoothing in `configs/constants.py`.

**Tracking feels laggy**

- Close other applications using the webcam.
- Use a lower camera resolution.

**Clicks are hard to trigger**

- Increase the pinch sensitivity threshold in `configs/constants.py`.

**Clicks trigger too often**

- Decrease the pinch sensitivity threshold in `configs/constants.py`.

**Volume control does not change system volume**

- Install `pycaw` and `comtypes`: `pip install pycaw comtypes`
- On non-Windows systems, volume control requires a different audio backend.

**Media keys do not work**

- Media keys are system-dependent. Ensure your media player supports keyboard media keys.

**Screenshots are not saving**

- Verify `assets/screenshots/` exists and is writable.

**Mode does not switch**

- Hold the activation gesture steadily for the full 2 second duration.
- Ensure your hand is fully visible and well-lit.
- Mode switching has a 1.5 second cooldown between switches.
