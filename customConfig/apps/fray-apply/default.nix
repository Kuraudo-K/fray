# Fray Apply - éditeur / apply Python (GTK)
# Source : GLF Config Editor, adapté (chemins FRAY_FLAKE, CLI fray-update)
# Le update-manager Rust GLF n'est pas porté ici (pas encore).
{
  config,
  pkgs,
  lib,
  ...
}:

let
  cfg = config.fray.apps.apply;
  iconName = "fray-apply";
  flakeDir =
    config.fray.system.nh.flake or "/home/kouro/Téléchargements/GLF pc/NIX/fray";

  pythonEnv = pkgs.python3.withPackages (ps: [ ps.pygobject3 ]);

  src = pkgs.runCommand "fray-apply-src" {
    nativeBuildInputs = [ pythonEnv ];
  } ''
    mkdir -p $out/share/icons/hicolor/{48x48,128x128,256x256}/apps
    cp ${./fray-apply.py} $out/fray-apply.py

    ${pythonEnv}/bin/python3 <<'PY'
import ast, base64, os

out = os.environ["out"]
src_path = os.path.join(out, "fray-apply.py")
with open(src_path, encoding="utf-8") as f:
    content = f.read()
start = content.index("_ICON_PNG_B64 = (")
end = content.index("\n)\n", start) + 2
ns = {}
exec(content[start:end], ns)
data = base64.b64decode(ns["_ICON_PNG_B64"])
for size in (48, 128, 256):
    d = os.path.join(out, "share", "icons", "hicolor", f"{size}x{size}", "apps")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "${iconName}.png"), "wb") as f:
        f.write(data)
PY
  '';

  frayApplyPkg = pkgs.stdenv.mkDerivation {
    pname = iconName;
    version = "0.1.0";

    inherit src;

    nativeBuildInputs = with pkgs; [
      wrapGAppsHook3
      gobject-introspection
      makeWrapper
    ];

    buildInputs = with pkgs; [
      gtk3
      glib
      pango
      gdk-pixbuf
      atk
      vte
      pythonEnv
    ];

    dontBuild = true;

    installPhase = ''
      runHook preInstall

      mkdir -p $out/bin $out/share/applications $out/share/fray-apply

      install -m 644 $src/fray-apply.py $out/share/fray-apply/
      cp -r $src/share/icons $out/share/

      iconPath="$out/share/icons/hicolor/256x256/apps/${iconName}.png"

      makeWrapper ${pythonEnv}/bin/python3 $out/bin/${iconName} \
        --add-flags "$out/share/fray-apply/fray-apply.py" \
        --set FRAY_APPLY_ICON "$iconPath" \
        --set-default FRAY_FLAKE ${lib.escapeShellArg flakeDir} \
        --prefix PATH : ${lib.makeBinPath (with pkgs; [ nix nh coreutils ])}

      cat > $out/share/applications/${iconName}.desktop <<'DESKTOP'
[Desktop Entry]
Name=Fray Apply
Comment=Éditeur / apply de la config Fray (customConfig)
Exec=fray-apply
Icon=fray-apply
Terminal=false
Type=Application
Categories=System;Settings;Administration;
Keywords=nix;nixos;config;fray;apply;
StartupWMClass=fray-apply
DESKTOP

      runHook postInstall
    '';
  };
in
{
  options.fray.apps.apply = {
    enable = lib.mkEnableOption "Fray Apply (éditeur Python / apply customConfig)";
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [ frayApplyPkg ];
  };
}
