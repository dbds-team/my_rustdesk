#!/bin/bash

# Flutter Rust Bridge generation script
set -e

echo "Generating Flutter Rust Bridge..."

# Install flutter_rust_bridge_codegen if not present
if ! command -v flutter_rust_bridge_codegen &> /dev/null; then
    echo "Installing flutter_rust_bridge_codegen..."
    cargo install flutter_rust_bridge_codegen --version 1.80.1 --features "uuid"
fi

# Generate bridge files
echo "Running flutter_rust_bridge_codegen..."
flutter_rust_bridge_codegen \
    --rust-input ../src/flutter_ffi.rs \
    --dart-output lib/generated_bridge.dart \
    --c-output generated_bridge.h

# Copy header files for different platforms
if [ -f "generated_bridge.h" ]; then
    cp generated_bridge.h ../flutter/macos/Runner/bridge_generated.h 2>/dev/null || true
    cp generated_bridge.h ../flutter/ios/Runner/bridge_generated.h 2>/dev/null || true
    echo "Bridge files generated successfully"
else
    echo "Warning: generated_bridge.h not found"
fi

echo "Flutter Rust Bridge generation completed"