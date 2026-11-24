# Khensoz Universal Media Downloader

A Windows desktop and mobile-friendly web interface powered by FastAPI, yt-dlp and FFmpeg. Only download media you own or are authorized to save. Platform restrictions and DRM are not bypassed.

## Windows
Download the latest **Windows-EXE** artifact from the [Actions](../../actions/workflows/windows-build.yml) workflow and extract it. Run `KhensozDownloader.exe`. For source use, install Python 3.11+ and run `start_windows.bat`.

Install FFmpeg using `winget install Gyan.FFmpeg`, then restart your terminal. FFmpeg must be on PATH for MP3 conversion and video merging. If using the compiled EXE, FFmpeg is still a separate prerequisite.

## Web / phone
Run `start_web_windows.bat` on the PC. On the same Wi-Fi, visit `http://YOUR-PC-IP:8765` from the phone, then use **Save to this device** after a download finishes. PC files are also saved in `Downloads/UniversalDownloader`. Never port-forward the server to the internet: the LAN web mode is unauthenticated. For private use only.

## CI
GitHub Actions runs Python compile checks and tests **before** Windows PyInstaller packaging, installs all dependencies **before** tests, packages the `static` directory, and uploads the EXE artifact. The build is deliberately lean: no broad `--collect-all` of unrelated optional modules. Artifacts are not signed, so Windows SmartScreen may warn. CI success verifies packaging, not that every external site currently permits downloads.
