#!/usr/bin/env bash
# Builds Gorsche as a GUI binary on macOS and Linux.
#
# Unlike Windows, Unix binaries have no separate "console" vs "GUI" linker
# subsystem, so a plain build already launches without allocating a console
# window. Running the resulting binary from a file manager (or wrapping it
# in a macOS .app bundle) opens the GUI directly, with no terminal attached.
set -euo pipefail

cd "$(dirname "$0")"

go build -o gorsche .

echo "Built gorsche"
