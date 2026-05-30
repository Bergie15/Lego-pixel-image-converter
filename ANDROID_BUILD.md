# Packaging the app as an Android APK

## What this does

Buildozer + python-for-android packages the existing Flask app into a standalone Android APK.
The APK starts Flask in a background thread on launch and displays the UI in a WebView.
No changes to the Flask routes, templates, or image processing logic are needed.

---

## Prerequisites (run on the Linux dev machine)

```bash
# Java (either 11 or 17 works)
sudo dnf install java-11-openjdk-devel

# System libs python-for-android needs to compile ARM binaries
sudo dnf install autoconf automake libtool pkg-config \
    zlib-devel libffi-devel openssl-devel \
    python3-devel gcc gcc-c++ make

# Buildozer itself
pip install buildozer
```

Buildozer downloads the Android SDK and NDK automatically on the first build (~1 GB).
Accept any SDK licence prompts that appear during the first run.

---

## Files to create (ask Claude to do this)

Tell Claude:
> "Set up the Buildozer config and Android entry point for this repo so I can build an APK.
> Use the webview bootstrap so the existing Flask UI works as-is."

Claude will create two files:

### 1. `buildozer.spec` (repo root)
Tells Buildozer the app name, package ID, which Python files/folders to include,
and which pip packages to bundle (flask, pillow, numpy, werkzeug).

### 2. `android_main.py` (repo root)
The Android entry point. Does two things:
- Starts `decor_planner/app.py` Flask server in a background thread on `localhost:5000`
- Opens an Android WebView pointed at `http://localhost:5000`

---

## Building the APK

```bash
cd /path/to/Lego-pixel-image-converter

# First build — slow (20–40 min), downloads SDK/NDK and compiles dependencies
buildozer android debug

# Subsequent builds — much faster (2–5 min)
buildozer android debug
```

The finished APK lands at:
```
bin/decorpixelplanner-<version>-arm64-v8a-debug.apk
```

---

## Installing on the phone

1. On the Android phone: Settings → Apps → Special app access → Install unknown apps
   → enable for your file manager or Chrome.
2. Copy the APK to the phone (USB cable, or `adb install bin/*.apk` if ADB is set up).
3. Tap the APK file on the phone and tap Install.

The app appears in the launcher like any other app.

---

## Known build gotchas

- **numpy** compiles from source for ARM — takes several minutes and occasionally fails
  on the first attempt. Run `buildozer android debug` again; it resumes where it left off.
  If it keeps failing, numpy can be removed from the spec — the app falls back gracefully
  (48-bit and 64-bit asset variants are skipped, everything else works).
- **Java version**: Buildozer works with Java 11 or 17. Java 21 may cause issues.
- **Disk space**: first build needs ~4 GB free for the SDK/NDK and build cache.
- **Rebuilding after code changes**: just re-run `buildozer android debug`.
  Only changed Python files are re-packaged; compiled C dependencies are cached.
