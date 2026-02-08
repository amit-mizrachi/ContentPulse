#!/bin/bash
# =============================================================================
# MOUNT NVMe STORAGE
# =============================================================================
# Detects, formats (if needed), and mounts NVMe instance storage.
# Must be run as root or with sudo.
#
# Usage: ./setup/02-mount-nvme.sh
#
# Configuration (from environment or AppConfig):
#   NVME_DEVICE      - NVMe device path (default: /dev/nvme1n1)
#   NVME_MOUNT_PATH  - Mount point (default: /mnt/nvme)
#   MODELS_DIR       - Models directory (default: /mnt/nvme/models)
# =============================================================================

set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${SCRIPTS_DIR}/lib/logger.sh"
source "${SCRIPTS_DIR}/lib/common.sh"
source "${SCRIPTS_DIR}/config/defaults.env"

# Load AppConfig if available
if [[ -f /tmp/appconfig_cache.json ]]; then
    source "${SCRIPTS_DIR}/lib/appconfig.sh"
    NVME_DEVICE=$(appconfig_get "judge_inference.storage.nvme_device" "$NVME_DEVICE")
    NVME_MOUNT_PATH=$(appconfig_get "judge_inference.storage.nvme_mount_path" "$NVME_MOUNT_PATH")
    MODELS_DIR=$(appconfig_get "judge_inference.storage.models_dir" "$MODELS_DIR")
fi

log_section "Mount NVMe Storage"

log_info "Device:     $NVME_DEVICE"
log_info "Mount path: $NVME_MOUNT_PATH"
log_info "Models dir: $MODELS_DIR"

# -----------------------------------------------------------------------------
# Check if running as root
# -----------------------------------------------------------------------------
if [[ $EUID -ne 0 ]]; then
    log_warn "Not running as root, some operations may fail"
    log_info "Consider running with: sudo $0"
fi

# -----------------------------------------------------------------------------
# Detect NVMe device
# -----------------------------------------------------------------------------
log_subsection "Detecting NVMe Device"

detect_nvme_device() {
    # Try configured device first
    if [[ -b "$NVME_DEVICE" ]]; then
        echo "$NVME_DEVICE"
        return 0
    fi

    # Auto-detect: find instance store NVMe (not the root volume)
    for device in /dev/nvme[0-9]n1; do
        if [[ -b "$device" ]]; then
            # Skip if it's the root device
            local root_device
            root_device=$(findmnt -n -o SOURCE / 2>/dev/null | sed 's/p[0-9]*$//' || echo "")
            if [[ "$device" != "$root_device" ]] && [[ "$device" != "${root_device}n1" ]]; then
                echo "$device"
                return 0
            fi
        fi
    done

    return 1
}

if ! DETECTED_DEVICE=$(detect_nvme_device); then
    die "No NVMe instance storage detected. Is this a GPU instance with local NVMe?"
fi

if [[ "$DETECTED_DEVICE" != "$NVME_DEVICE" ]]; then
    log_warn "Using detected device: $DETECTED_DEVICE (configured: $NVME_DEVICE)"
    NVME_DEVICE="$DETECTED_DEVICE"
fi

log_success "Found NVMe device: $NVME_DEVICE"

# Show device info
if command -v lsblk &>/dev/null; then
    log_info "Device info:"
    lsblk "$NVME_DEVICE" 2>/dev/null || true
fi

# -----------------------------------------------------------------------------
# Check if already mounted
# -----------------------------------------------------------------------------
log_subsection "Checking Mount Status"

if mountpoint -q "$NVME_MOUNT_PATH" 2>/dev/null; then
    log_success "Already mounted at: $NVME_MOUNT_PATH"

    # Verify it's the right device
    MOUNTED_DEVICE=$(findmnt -n -o SOURCE "$NVME_MOUNT_PATH" 2>/dev/null || echo "")
    if [[ "$MOUNTED_DEVICE" == "$NVME_DEVICE" ]]; then
        log_info "Correct device is mounted"
    else
        log_warn "Different device mounted: $MOUNTED_DEVICE"
    fi

    # Ensure models directory exists
    ensure_dir "$MODELS_DIR"
    chmod 777 "$MODELS_DIR" 2>/dev/null || true

    log_success "NVMe storage ready"
    exit 0
fi

log_info "Not currently mounted, proceeding with setup..."

# -----------------------------------------------------------------------------
# Format if needed
# -----------------------------------------------------------------------------
log_subsection "Checking Filesystem"

FS_TYPE=$(blkid -o value -s TYPE "$NVME_DEVICE" 2>/dev/null || echo "")

if [[ -z "$FS_TYPE" ]]; then
    log_info "No filesystem detected, formatting with ext4..."

    if ! command -v mkfs.ext4 &>/dev/null; then
        die "mkfs.ext4 not found. Install e2fsprogs."
    fi

    mkfs.ext4 -F "$NVME_DEVICE" || die "Failed to format $NVME_DEVICE"
    log_success "Formatted with ext4"
elif [[ "$FS_TYPE" == "ext4" ]]; then
    log_success "ext4 filesystem already exists"
else
    log_warn "Existing filesystem: $FS_TYPE"
    if ! confirm "Format with ext4? This will ERASE all data!" "n"; then
        die "Aborted. Cannot mount non-ext4 filesystem."
    fi
    mkfs.ext4 -F "$NVME_DEVICE" || die "Failed to format $NVME_DEVICE"
    log_success "Reformatted with ext4"
fi

# -----------------------------------------------------------------------------
# Mount
# -----------------------------------------------------------------------------
log_subsection "Mounting Filesystem"

ensure_dir "$NVME_MOUNT_PATH"

mount "$NVME_DEVICE" "$NVME_MOUNT_PATH" || die "Failed to mount $NVME_DEVICE at $NVME_MOUNT_PATH"

log_success "Mounted at: $NVME_MOUNT_PATH"

# -----------------------------------------------------------------------------
# Add to fstab (for persistence)
# -----------------------------------------------------------------------------
log_subsection "Configuring Persistence"

FSTAB_ENTRY="$NVME_DEVICE $NVME_MOUNT_PATH ext4 defaults,nofail 0 2"

if grep -q "$NVME_MOUNT_PATH" /etc/fstab 2>/dev/null; then
    log_info "Mount already in /etc/fstab"
else
    log_info "Adding to /etc/fstab..."
    echo "$FSTAB_ENTRY" >> /etc/fstab || log_warn "Could not update /etc/fstab (not running as root?)"
    log_success "Added to /etc/fstab"
fi

# -----------------------------------------------------------------------------
# Create directories
# -----------------------------------------------------------------------------
log_subsection "Creating Directories"

ensure_dir "$MODELS_DIR"
chmod 777 "$MODELS_DIR"

log_success "Created: $MODELS_DIR"

# -----------------------------------------------------------------------------
# Show final status
# -----------------------------------------------------------------------------
log_subsection "Summary"

df -h "$NVME_MOUNT_PATH"

log_success "NVMe storage ready!"
log_info "Models directory: $MODELS_DIR"
