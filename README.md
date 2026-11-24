# Khensoz Universal Media Downloader

A Windows desktop and mobile-friendly web interface powered by FastAPI, yt-dlp and FFmpeg. Only download media you own or are authorized to save. Platform restrictions and DRM are not bypassed.

## Windows
Download the latest **Windows-EXE** artifact from the [Actions](../../actions/workflows/windows-build.yml) workflow and extract it. Run `KhensozDownloader.exe`. For source use, install Python 3.11+ and run `start_windows.bat`.

Install FFmpeg using `winget install Gyan.FFmpeg`, then restart your terminal. FFmpeg must be on PATH for MP3 conversion and video merging. If using the compiled EXE, FFmpeg is still a separate prerequisite.

## Save location
On Windows, the default destination is `D:\\Khensoz Transfer\\Universal Downloader`. The desktop app's **Choose PC save folder** button opens a native folder picker and remembers your selection for future launches. Completed downloads are automatically placed in the chosen folder. **Save to this device** on desktop opens a Save As dialog and confirms success only after the copy finishes. On phones and web browsers, **Save to this device** initiates a browser download and shows a download-started message; browser security prevents the app from confirming the final destination.

## Web / phone
Run `start_web_windows.bat` on the PC. On the same Wi-Fi, visit `http://YOUR-PC-IP:8765` from the phone, then use **Save to this device** after a download finishes. PC files are also saved in `Downloads/UniversalDownloader`. Never port-forward the server to the internet: the LAN web mode is unauthenticated. For private use only.

## CI
GitHub Actions runs Python compile checks and tests **before** Windows PyInstaller packaging, installs all dependencies **before** tests, packages the `static` directory, and uploads the EXE artifact. The build is deliberately lean: no broad `--collect-all` of unrelated optional modules. Artifacts are not signed, so Windows SmartScreen may warn. CI success verifies packaging, not that every external site currently permits downloads.

## Installable PWA
The web UI now includes a manifest, app icon, service worker and an install prompt on compatible browsers. For Android/Windows use the browser's Install app option; on iPhone use Safari's Share → Add to Home Screen. **Important:** modern browsers require a secure context (HTTPS or localhost) for service workers, installation and the browser folder picker. Opening `http://YOUR-PC-IP:8765` over Wi-Fi still works as a normal website but generally **cannot be installed as a PWA**. To install it on your phone, serve the same local backend through a trusted HTTPS reverse proxy/tunnel (with access control); do not expose the unauthenticated downloader publicly. Offline mode caches only the UI shell; media downloads require the Python server.

On supported Chromium browsers over HTTPS, choose **Choose browser save folder** before saving. Once writing completes, the app confirms the saved file. On iOS and browsers without the File System Access API, **Save to this device** triggers the browser download; the app cannot verify the final save location.
