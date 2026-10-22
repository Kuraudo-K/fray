# Script de bump faugus-version.nix (chemin flake Fray, pas /etc/nixos)
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.gaming.faugusUpdate;
  flakeDir = config.fray.system.nh.flake or "/home/kouro/Téléchargements/GLF pc/NIX/fray";
  versionRel = "customConfig/gaming/launchers/faugus-version.nix";
in
{
  options.fray.gaming.faugusUpdate = {
    enable = lib.mkEnableOption "Script that bumps faugus-version.nix from GitHub releases";
  };

  config = lib.mkIf cfg.enable {
    environment.etc."fray/faugus-update/check-faugus.sh" = {
      mode = "0755";
      text = ''
        #!${pkgs.bash}/bin/bash
        set -euo pipefail
        VERSION_FILE="${flakeDir}/${versionRel}"
        CURRENT=$(${pkgs.gnugrep}/bin/grep -oP 'version = "\K[^"]+' "$VERSION_FILE" || echo "0.0.0")
        LATEST=$(${pkgs.curl}/bin/curl -s https://api.github.com/repos/Faugus/faugus-launcher/releases/latest \
          | ${pkgs.jq}/bin/jq -r '.tag_name')
        if [ -z "$LATEST" ] || [ "$LATEST" = "null" ]; then
          echo "[WARN] API GitHub Faugus injoignable, on garde $CURRENT" >&2
          exit 0
        fi
        if [ "$LATEST" = "$CURRENT" ]; then
          echo "[INFO] Faugus déjà à jour ($CURRENT)" >&2
          exit 0
        fi
        echo "[INFO] Faugus : $CURRENT -> $LATEST" >&2
        HASH=$(${pkgs.nix-prefetch-github}/bin/nix-prefetch-github Faugus faugus-launcher --rev "$LATEST" \
          | ${pkgs.jq}/bin/jq -r '.hash')
        cat > "$VERSION_FILE" <<EOF
        # Pin Faugus GitHub — généré par check-faugus.sh
        {
          version = "$LATEST";
          hash = "$HASH";
        }
        EOF
        echo "[INFO] $VERSION_FILE -> $LATEST (rebuild Fray ensuite)" >&2
      '';
    };

    environment.systemPackages = [
      (pkgs.writeShellApplication {
        name = "fray-faugus-update";
        text = ''exec /etc/fray/faugus-update/check-faugus.sh "$@"'';
      })
    ];
  };
}
