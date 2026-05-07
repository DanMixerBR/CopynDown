<div align="center">
  <img src="assets/logo_c.png" alt="CopynDown Logo" width="150">
  <h1>CopynDown</h1>
  <p>
    <a href="https://github.com/DanMixerBR/CopynDown/releases/latest"><img src="https://img.shields.io/badge/version-2.6.0-blue.svg?style=for-the-badge"></a>
    <a href="https://img.shields.io/badge/platform-Windows%20%7C%20Linux-blue.svg"><img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux-blue.svg?style=for-the-badge"></a>
    <a href="https://www.python.org/downloads/release/python-3120/"><img src="https://img.shields.io/badge/Python-3.12-blue.svg?style=for-the-badge&logo=python&logoColor=white"></a>
    <br>
    <a href="DONATE.md"><img src="https://img.shields.io/badge/Donate-Support_CopynDown-blue?style=for-the-badge&logo=githubsponsors&logoColor=red" alt="Donate"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="License MIT"></a>
  </p>
  <p>A modern, fast, and cross-platform media downloader and converter.</p>
  <p><b>Developed with 💻 by DanMixerBR</b></p>
</div>

## 🌟 Features

* **Modern GUI:** Clean and intuitive interface with native Dark Mode.
* **Cross-Platform:** Built to work seamlessly on both Windows and Linux.
* **Versatile Downloads:** Support for individual links and full playlists.
* **Built-in Converter:** Easily convert downloaded media into various formats.
* **High Quality:** Download videos up to 4K resolution and audio up to 320 kbps.

## 📸 Screenshots

<p align="center">
  <img src="assets/windows_ui.png" alt="Windows Interface" width="50%">
  <br>
  <em>CopynDown running on Windows.</em>
</p>

<p align="center">
  <img src="assets/linux_ui.png" alt="Linux Interface" width="50%">
  <br>
  <em>CopynDown running on Linux.</em>
</p>

## ⚙️ Supported Sites, Formats & Resolutions

**Supported sites:** YouTube, Vimeo, Dailymotion, Twitch, Instagram, TikTok, Kwai, Facebook, Twitter/X, Reddit, SoundCloud, LinkedIn, Pinterest, Snapchat, Bilibili, Rumble, Bandcamp, Mixcloud, Kick, and Odysee.

**Supported video resolutions:** 2160p (4K), 1440p (QHD), 1080p (Full HD), 720p, 480p, and 360p.

**Supported audio bitrates:** 320 kbps, 256 kbps, 192 kbps, and 128 kbps.

**Supported download formats:**
* Video: MP4, MKV, and WEBM.
* Audio: M4A, MP3, FLAC, WAV, and Opus.

**Supported conversion formats:**
* Video: MP4, MKV, WEBM, MOV, and AVI.
* Audio: M4A, MP3, FLAC, WAV, Opus, and Ogg.

## 📥 Installation

### Windows
1. Download the latest release of [CopynDown_Windows.zip](https://github.com/DanMixerBR/CopynDown/releases/latest/download/CopynDown_Windows.zip).
2. Extract the downloaded `.zip` file to your preferred folder.
3. Double-click the `CopynDown.exe` file to run the application.

### Linux
1. Download the latest release of [CopynDown_Linux.zip](https://github.com/DanMixerBR/CopynDown/releases/latest/download/CopynDown_Linux.zip).
2. Extract the downloaded `.zip` file.
3. Right-click the `Install_CopynDown.sh` and select **"Run as a program"** (or run it via terminal).
4. Right-click `CopynDown` shortcut and select **"Allow Launching"** to run the application.

> **Note:** The Linux installation script will automatically configure the required environment and create a convenient shortcut on both your Desktop and your Application Menu!

## 🍪 Authentication & Cookies (Age-Restricted/Private Content)

Some platforms (like YouTube, Instagram, and TikTok) require an active login session to verify your age or subscription status before allowing you to view or download specific media. 

CopynDown makes this easy with a built-in **Native Cookie Extractor**. You don't need to install any shady browser extensions!

**How to extract and use your cookies:**
1. Open your regular web browser and log in to the desired platform (e.g., youtube.com, instagram.com).
2. Open **CopynDown** and click the **⚙ Settings** button.
3. Scroll down to the **"Auto-extract cookies"** section.
4. Select your web browser from the dropdown list and click **"Extract cookies"**.
5. CopynDown will safely extract your current session directly from your browser and save it locally in the `bin` folder. 

You can now download age-restricted and private content seamlessly!

> **⚠️ Troubleshooting - Cookie Extraction Failed:**
> *   **Admin Rights (Chrome/Edge v130+):** Due to modern security updates (App-Bound Encryption), Windows may block external apps from reading browser data. If the extraction fails, close CopynDown, right-click the `CopynDown.exe` icon, select **"Run as Administrator"**, and try again.
> *   **Browser Lock:** Ensure the selected browser is completely closed before extracting, as some browsers lock their database while running.

## 🛡️ Troubleshooting

### Windows SmartScreen Warning (False Positive)
When running CopynDown for the first time on Windows, you might encounter a blue **Windows Defender SmartScreen** stating that it "protected your PC" from an unrecognized app.

**Why does this happen?**
CopynDown is an independent, open-source project. Because we haven't purchased an expensive Code Signing Certificate, Windows flags the `.exe` as an "Unknown Publisher" simply because it is new. 

**How to run CopynDown safely:**
It is completely safe to bypass this warning. To do so:
1. Click on **"More info"** at the end of the paragraph.
2. A new button will appear at the bottom. Click on **"Run anyway"**.

<img src="assets/SmartScreen_Bypass_1.png" alt="Windows Interface" width="50%">
<img src="assets/SmartScreen_Bypass_2.png" alt="Windows Interface" width="50%">

*Note: You will only need to do this once. If you want to verify the safety of the application, feel free to inspect the open-source code in this repository.*

## 🛠️ Build from Source

If you are a developer and want to run CopynDown directly from the Python source code:

1. Clone this repository:
   ```bash
   git clone https://github.com/DanMixerBR/CopynDown.git
   ```
2. Navigate to the project directory:
   ```bash
   cd CopynDown
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python main.py
   ```

## 👨‍💻 Author

**DanMixerBR**  
*Creator and Lead Developer*  
If you have any questions, suggestions, or just want to say hi, feel free to reach out!
* GitHub: [@DanMixerBR](https://github.com/DanMixerBR)

## ⚖️ Credits & License

This project is built using:
* [Python](https://www.python.org/)
* [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for the modern UI.
* [yt-dlp](https://github.com/yt-dlp/yt-dlp) for media downloading.
* [FFmpeg](https://ffmpeg.org/) for media conversion.
* [Deno](https://deno.com/) as the JavaScript runtime for executing complex extraction scripts.

This project is licensed under the MIT License - see the LICENSE file for details.
