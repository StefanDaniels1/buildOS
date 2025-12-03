#!/bin/bash
# Quick verification script to check if file upload fix is working

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                   FILE UPLOAD FIX - VERIFICATION                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check latest log file
LATEST_LOG=$(ls -t .logs/conversations/*.jsonl 2>/dev/null | head -1)

if [ -z "$LATEST_LOG" ]; then
    echo "❌ No log files found"
    echo "   Please run a session first!"
    exit 1
fi

echo "📄 Latest log file: $(basename $LATEST_LOG)"
echo ""

# Check for file_path and available_files
echo "🔍 Checking file upload status..."
echo ""

# Get the system_context event which has the file info
SYSTEM_CONTEXT=$(grep '"event": "system_context"' "$LATEST_LOG" | tail -1)

if [ -z "$SYSTEM_CONTEXT" ]; then
    echo "⚠️  No system_context event found in log"
    echo ""
else
    echo "System context found:"
    echo "$SYSTEM_CONTEXT" | jq .
    echo ""
    
    FILE_PATH=$(echo "$SYSTEM_CONTEXT" | jq -r '.file_path')
    AVAILABLE_FILES_COUNT=$(echo "$SYSTEM_CONTEXT" | jq -r '.available_files | length')
    
    echo "file_path: $FILE_PATH"
    echo "available_files count: $AVAILABLE_FILES_COUNT"
    echo ""
    
    if [ "$FILE_PATH" != "null" ] || [ "$AVAILABLE_FILES_COUNT" != "0" ]; then
        echo "✅ FIX IS WORKING!"
        echo ""
        echo "   Files are being passed to orchestrator correctly."
        if [ "$FILE_PATH" != "null" ]; then
            echo "   file_path: $FILE_PATH"
        fi
        if [ "$AVAILABLE_FILES_COUNT" != "0" ]; then
            echo "   available_files: $AVAILABLE_FILES_COUNT file(s)"
            echo "$SYSTEM_CONTEXT" | jq -r '.available_files[]'
        fi
        echo ""
    else
        echo "❌ FIX NOT APPLIED YET"
        echo ""
        echo "   Both file_path and available_files are empty!"
        echo ""
        echo "   Troubleshooting steps:"
        echo "   1. Check browser console for frontend logs (F12)"
        echo "   2. Check server logs for backend received data"
        echo "   3. Make sure frontend was rebuilt: cd apps/client && bun run dev"
        echo "   4. Hard refresh browser: Cmd+Shift+R"
        echo "   5. Upload file and send message again"
        echo ""
    fi
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Full analysis:"
echo "   python analyze_logs.py --analyze 0"
echo ""
