# GestureOS Controls

## Quick Start

1. Run the application:

```bash
python main.py
```

2. Show your hand to the webcam.
3. Use the gestures below to control your computer.

---

## Current Controls

| Gesture                             | Action            |
| ----------------------------------- | ----------------- |
| Move index finger                   | Move mouse cursor |
| Thumb + Index finger pinch          | Left click        |
| Thumb + Middle finger pinch         | Right click       |
| Two fingers up (Index above Middle) | Scroll up         |
| Two fingers up (Middle above Index) | Scroll down       |
| Closed fist (hold 2 seconds)        | Exit application  |
| Q key                               | Exit application  |

---

## How It Works

### Mouse Movement

Raise your index finger and move your hand to control the mouse cursor.

### Left Click

Pinch your thumb and index finger together.

### Right Click

Pinch your thumb and middle finger together.

### Scrolling

Extend your index and middle fingers.

* Index finger higher than middle finger → Scroll Up
* Middle finger higher than index finger → Scroll Down

### Exit

Make a closed fist and hold it for 2 seconds.

You can also press **Q** on your keyboard to close the application.

---

## Current Features

✅ Real-time hand tracking

✅ Mouse cursor control

✅ Left click

✅ Right click

✅ Scrolling

✅ Safe exit gesture

---

## Planned Features

🚀 Volume Control

🚀 Screenshot Capture

🚀 Media Controls

🚀 Presentation Mode

🚀 Gaming Mode

🚀 Custom Gestures

🚀 Gesture Analytics

🚀 AI Gesture Recognition

---

## Tips

* Use good lighting for better tracking.
* Keep your hand inside the camera frame.
* Use the default 640×480 resolution for best performance.
* Press **Q** if you need to exit quickly.

---

## Troubleshooting

**Cursor feels slow**

* Reduce cursor smoothing in `configs/constants.py`.

**Tracking feels laggy**

* Close other applications using the webcam.
* Use a lower camera resolution.

**Clicks are hard to trigger**

* Increase the pinch sensitivity threshold.

**Clicks trigger too often**

* Decrease the pinch sensitivity threshold.
