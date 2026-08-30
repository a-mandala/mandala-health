#!/usr/bin/env bash
# Install the mandala-health systemd *user* service on urano.
# No sudo required: everything lives under ~/.config/systemd/user/.
#
# Prerequisites (checked):
#   - uv available in PATH (usually ~/.local/bin/uv)
#   - repo cloned at ~/workspace/mandala-health (with .venv created by `uv sync`)
#
# After running this script, the service is enabled and started.
#
# LIMITS (require Alessandro's action):
#   - The user service only runs while there is an active login session.
#     To keep it running at boot / after logout, once (with password):
#         loginctl enable-linger $USER
#     (this step CANNOT be automated without sudo/polkit rules).

set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/workspace/mandala-health}"
UNIT_NAME="mandala-health.service"
UNIT_SRC="$REPO_DIR/deploy/$UNIT_NAME"
UNIT_DST="$HOME/.config/systemd/user/$UNIT_NAME"

command -v uv >/dev/null 2>&1 || { echo "ERROR: uv not found in PATH" >&2; exit 1; }
[ -f "$UNIT_SRC" ] || { echo "ERROR: $UNIT_SRC not found" >&2; exit 1; }

mkdir -p "$HOME/.config/systemd/user"
cp "$UNIT_SRC" "$UNIT_DST"

systemctl --user daemon-reload
systemctl --user enable --now "$UNIT_NAME"

echo
echo "Installed and started $UNIT_NAME (user service)."
echo "Check:    systemctl --user status $UNIT_NAME"
echo "Logs:     journalctl --user -u $UNIT_NAME -f"
echo
echo "If the service must survive logout/reboot, run ONCE:"
echo "  loginctl enable-linger \$USER"
