# metaidigitcv

## 🚀 Hand Tracking & Gesture Recognition with metaidigitcv

**metaidigitcv** is an advanced computer vision and machine learning library designed to detect, track, and analyze hand keypoints using **MediaPipe** and **OpenCV**. Whether you're building interactive applications, gesture-based controls, or AI-powered hand recognition systems, metaidigitcv simplifies the process with efficient hand tracking and keypoint extraction.

---

## 🔥 Features

✅ **Hand Detection** – Accurately detects multiple hands in real-time.  
✅ **Landmark Tracking** – Tracks 21 keypoints per hand.  
✅ **Finger Recognition** – Identifies raised fingers for gesture recognition.  
✅ **Distance Measurement** – Computes distance between two keypoints.  
✅ **Optimized Performance** – Uses MediaPipe for fast processing.  

---

## 📦 Installation

```bash
pip install metaidigitcv
```

Ensure you have **OpenCV** and **MediaPipe** installed:

```bash
pip install opencv-python mediapipe numpy
```

---

## 🎯 Quick Start

```python
import cv2
from metaidigitcv.main import Handtracker

# Initialize the tracker
detector = Handtracker()

# Capture video
cap = cv2.VideoCapture(0)

while True:
    success, img = cap.read()
    if not success:
        break
    
    hands, img = detector.identifyHands(img)
    if hands:
        lmList = hands[0]["lmList"]  # List of hand landmarks
        print("Thumb Tip Position:", lmList[4])
    
    cv2.imshow("Hand Tracking", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

---

## ✨ Key Functions

### 🖐 Hand Detection
```python
hands, img = detector.identifyHands(img, draw=True)
```
- Detects hands in an image/video frame.
- Draws hand landmarks if `draw=True`.

### 🏷️ Landmark Extraction
```python
lmList, bbox = detector.trackPosition(img)
```
- Returns a list of hand landmark positions.
- Provides the bounding box of the detected hand.

### ✋ Finger State Detection
```python
fingers = detector.trackRaisedFingers(hands[0])
```
- Returns a list `[1, 0, 1, 1, 0]` where `1` means the finger is up.

### 📏 Distance Calculation
```python
length, img, points = detector.trackDistance(4, 8, img)
```
- Measures the Euclidean distance between two keypoints (e.g., thumb and index finger).

---

## 🎯 Applications

🔹 **Gesture-based UI controls** 🎮  
🔹 **Sign language recognition** 🤟  
🔹 **Virtual painting & drawing** 🎨  
🔹 **Touchless interaction systems** 🤖  
🔹 **AI-powered hand gesture games** 🎭  

---

## 📜 License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

We welcome contributions! Feel free to fork the repository and submit a pull request.

---

## 📧 Contact

👤 **Author:** Suhal Samad  
✉️ Email: [samadsuhal@gmail.com](mailto:samadsuhal@gmail.com)  

If you like **metaidigitcvcv**, don't forget to ⭐ the repository!

---

🚀 **Let's build amazing hand-tracking applications together!** 🚀

