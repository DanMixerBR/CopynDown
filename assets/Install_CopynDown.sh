#!/bin/bash

# 1. Get the exact directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 2. Define the paths
DESKTOP_FILE="$HOME/.local/share/applications/copyndown.desktop"
USER_DESKTOP=$(xdg-user-dir DESKTOP)

chmod +x "$DIR/core/CopynDown"
chmod +x "$DIR/core/bin/yt-dlp"
chmod +x "$DIR/core/bin/ffmpeg"
chmod +x "$DIR/core/bin/ffprobe"
chmod +x "$DIR/core/bin/deno"

# 3. Create the shortcut file injecting the absolute paths
echo "[Desktop Entry]" > "$DESKTOP_FILE"
echo "Name=CopynDown" >> "$DESKTOP_FILE"
echo "Comment=Media Downloader and Converter" >> "$DESKTOP_FILE"
echo "Exec=\"$DIR/core/CopynDown\"" >> "$DESKTOP_FILE"
echo "Path=$DIR/core" >> "$DESKTOP_FILE"
echo "Icon=$DIR/core/bin/icon.png" >> "$DESKTOP_FILE"
echo "Terminal=false" >> "$DESKTOP_FILE"
echo "Type=Application" >> "$DESKTOP_FILE"
echo "Categories=AudioVideo;Utility;" >> "$DESKTOP_FILE"
echo "StartupWMClass=CopynDown" >> "$DESKTOP_FILE"

# 4. Give execution permission to the menu shortcut
chmod +x "$DESKTOP_FILE"

# 5. Copy the shortcut to the Desktop and make it executable
if [ -d "$USER_DESKTOP" ]; then
    cp "$DESKTOP_FILE" "$USER_DESKTOP/"
    chmod +x "$USER_DESKTOP/copyndown.desktop"
fi

echo "================================================="
echo " Success! Shortcut added to Application Menu"
echo " AND copied to your Desktop."
echo "================================================="
sleep 4
