# NEXORA — Known Limitations & Boundaries

## 1. Device & OS Boundaries
- **Xiaomi HyperOS Touch Security**: Simulating touch via ADB (`input tap`) on Xiaomi devices requires toggling "USB Debugging (Security settings)" in Developer Options. This requires a Mi account to be signed in on the phone initially.
- **Dynamic Video Audio Transcription**: Full video audio transcription requires real-time audio loopback capture or exporting video files. Nexora currently extracts displayed on-screen text, captions, and available audio metadata. Full offline Whisper audio transcription can be added as an optional plugin.
- **DRM Protected Screens**: Applications with `FLAG_SECURE` enabled (such as banking apps or protected streaming content) will return blank/black framebuffers from `screencap`.

## 2. Platform Boundaries
- **USB Cable Dependent Latency**: Screenshot capture over high-speed USB 3.0 runs in ~300ms, while wireless ADB on saturated Wi-Fi networks may introduce 1-2s latency per capture.
