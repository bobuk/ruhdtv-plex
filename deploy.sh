#!/bin/sh
B="$HOME/Library/Application Support/Plex Media Server/Plug-ins/hdouttv.bundle"
test -d "$B" || B="$HOME/Library/Application Support/Plex Media Server/Plug-ins/hdouttv.bundle"
I="$B/Contents"
mkdir -p "$B/"
cp -r "Contents" "$B/"

echo "Done. God bless git and Linus."
