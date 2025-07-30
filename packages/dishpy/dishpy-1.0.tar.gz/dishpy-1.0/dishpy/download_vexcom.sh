#!/bin/bash

# Check if target directory is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <target_directory>"
    echo "Example: $0 /home/user/.cache/DishPy/dishpy"
    exit 1
fi

TARGET_DIR="$1"

# Create target directory if it doesn't exist
mkdir -p "$TARGET_DIR"

echo "⬇️ Downloading VEX extension bundle..."
curl -L --progress-bar https://openvsxorg.blob.core.windows.net/resources/VEXRobotics/vexcode/0.6.1/VEXRobotics.vexcode-0.6.1.vsix -o vexcode.vsix

echo "📦 Extracting extension files..."
unzip -q vexcode.vsix && rm vexcode.vsix

echo "📂 Copying VEXcom tools to $TARGET_DIR..."
cp -r extension/resources/tools/vexcom "$TARGET_DIR/"

echo "🧹 Cleaning up temporary files..."
rm -f "[Content_Types].xml" extension.vsixmanifest
rm -rf extension

echo "✅ VEXcom tools installed successfully to $TARGET_DIR/vexcom"