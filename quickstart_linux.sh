#!/bin/bash
echo "+------------------------------------------------+"
echo "[               Fashion                          ]"
echo "[                   Previewer                    ]"
echo "[                       Launcher                 ]"
echo "+------------------------------------------------+"
echo 
echo "Lovingly made by:"
echo "KusangiKyo, Dino, Yuki, Arketual, and Mewsie."
echo
echo "From CoraTO, on behalf of the Trickster community."
echo "Thank you for everything :3"
echo 
echo "+------------------------------------------------+"
echo

# Change to the directory where this script is located
cd "$(dirname "$0")"

echo "Starting Fashion Previewer..."
echo
cd src
$PYTHON_CMD launch_previewer.py
cd ..

if [ $? -ne 0 ]; then
    echo
    echo "ERROR: The application crashed or failed to start!"
    echo "This might be due to missing dependencies."
    echo "Try running: pip3 install Pillow"
    read -p "Press Enter to exit..."
    exit 1
fi
