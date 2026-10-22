# Mise à jour système (CLI)
# Sur hôte GLF : délègue à glf-update ; sinon refuse un rebuild hôte
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.services.updateManager;

  frayUpdate = pkgs.writeShellApplication {
    name = "fray-update";
    runtimeInputs = with pkgs; [
      coreutils
      nix
    ];
    text = ''
      #!/usr/bin/env bash
      set -euo pipefail
      if [ -x /run/current-system/sw/bin/glf-update ]; then
        exec /run/current-system/sw/bin/glf-update "$@"
      fi
      if command -v glf-switch >/dev/null 2>&1; then
        exec glf-switch "$@"
      fi
      FLAKE_DIR="''${FRAY_FLAKE:-/home/kouro/Téléchargements/GLF pc/NIX/fray}"
      if [ -f "$FLAKE_DIR/flake.nix" ]; then
        echo "[Fray] Tests = VM seulement. Rebuild hôte interdit."
        echo "[Fray] Use: cd \"$FLAKE_DIR\" && nix build .#vm"
        exit 2
      fi
      echo "[Fray] Pas de glf-update / flake. Exporte FRAY_FLAKE=…" >&2
      exit 1
    '';
  };
in
{
  options.fray.services.updateManager = {
    enable = lib.mkEnableOption "fray-update CLI (delegates or refuses host rebuild)";
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [ frayUpdate ];
  };
}
