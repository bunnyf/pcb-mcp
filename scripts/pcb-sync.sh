#!/bin/bash
# pcb-sync: Sync PCB projects between local and VPS
# Usage: pcb-sync push|pull <project> [vps-host]

set -e

# Configuration - modify these or set env vars
VPS_HOST="${PCB_VPS_HOST:-pcb-vps}"
LOCAL_BASE="${PCB_LOCAL_BASE:-$HOME/workdir/pcb}"
REMOTE_BASE="${PCB_REMOTE_BASE:-/root/pcb/projects}"

usage() {
    echo "Usage: pcb-sync <command> <project> [vps-host]"
    echo ""
    echo "Commands:"
    echo "  push    Upload project to VPS"
    echo "  pull    Download output from VPS"
    echo "  status  Show sync status"
    echo ""
    echo "Examples:"
    echo "  pcb-sync push my_board"
    echo "  pcb-sync pull my_board"
    echo "  pcb-sync push my_board user@vps.example.com"
    echo ""
    echo "Environment variables:"
    echo "  PCB_VPS_HOST    - VPS hostname (default: pcb-vps)"
    echo "  PCB_LOCAL_BASE  - Local projects dir (default: ~/workdir/pcb)"
    echo "  PCB_REMOTE_BASE - Remote projects dir (default: /root/pcb/projects)"
    exit 1
}

if [ $# -lt 2 ]; then
    usage
fi

CMD=$1
PROJECT=$2
VPS_HOST="${3:-$VPS_HOST}"

LOCAL_DIR="$LOCAL_BASE/$PROJECT"
REMOTE_DIR="$REMOTE_BASE/$PROJECT"

case $CMD in
    push)
        if [ ! -d "$LOCAL_DIR" ]; then
            echo "Error: Local project not found: $LOCAL_DIR"
            exit 1
        fi
        
        echo "Uploading $PROJECT to $VPS_HOST..."
        echo "  Local:  $LOCAL_DIR"
        echo "  Remote: $REMOTE_DIR"
        
        # Create remote dir
        ssh "$VPS_HOST" "mkdir -p $REMOTE_DIR"
        
        # Sync (exclude output, backups)
        rsync -avz --progress \
            --exclude 'output/' \
            --exclude '*-backups/' \
            --exclude '*.kicad_pcb-bak' \
            --exclude '*.kicad_sch-bak' \
            --exclude 'fp-info-cache' \
            "$LOCAL_DIR/" "$VPS_HOST:$REMOTE_DIR/"
        
        echo "✅ Push complete"
        ;;
        
    pull)
        echo "Downloading output from $VPS_HOST..."
        echo "  Remote: $REMOTE_DIR/output"
        echo "  Local:  $LOCAL_DIR/output"
        
        # Create local output dir
        mkdir -p "$LOCAL_DIR/output"
        
        # Sync output only
        rsync -avz --progress \
            "$VPS_HOST:$REMOTE_DIR/output/" "$LOCAL_DIR/output/"
        
        echo "✅ Pull complete"
        
        # List downloaded files
        echo ""
        echo "Downloaded files:"
        find "$LOCAL_DIR/output" -type f -newer "$LOCAL_DIR/output" 2>/dev/null | head -20 || \
        ls -la "$LOCAL_DIR/output/"
        ;;
        
    status)
        echo "Project: $PROJECT"
        echo "VPS: $VPS_HOST"
        echo ""
        
        echo "Local files:"
        if [ -d "$LOCAL_DIR" ]; then
            ls -la "$LOCAL_DIR/"
        else
            echo "  (not found)"
        fi
        
        echo ""
        echo "Remote files:"
        ssh "$VPS_HOST" "ls -la $REMOTE_DIR/ 2>/dev/null || echo '  (not found)'"
        
        echo ""
        echo "Remote output:"
        ssh "$VPS_HOST" "ls -la $REMOTE_DIR/output/ 2>/dev/null || echo '  (not found)'"
        ;;
        
    *)
        usage
        ;;
esac
