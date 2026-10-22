# Fray Editor Config - éditeur / apply Python (GTK)
# Source : GLF Config Editor, adapté (chemins FRAY_FLAKE, CLI fray-update)
# Icône : 04gr10-charcoal-crimson
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

  # Logo officiel charcoal-crimson (pas le seal)
  iconSrc = ../../branding/assets/logo/04gr10-charcoal-crimson.png;

  frayApplyPkg = pkgs.stdenv.mkDerivation {
    pname = iconName;
    version = "0.2.0";

    dontUnpack = true;

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

    installPhase = ''
      runHook preInstall

      mkdir -p $out/bin $out/share/applications $out/share/fray-apply
      mkdir -p $out/share/icons/hicolor/{48x48,128x128,256x256,512x512}/apps

      install -m 644 ${./fray-apply.py} $out/share/fray-apply/fray-apply.py
      install -m 644 ${iconSrc} $out/share/icons/hicolor/512x512/apps/${iconName}.png
      install -m 644 ${iconSrc} $out/share/icons/hicolor/256x256/apps/${iconName}.png
      install -m 644 ${iconSrc} $out/share/icons/hicolor/128x128/apps/${iconName}.png
      install -m 644 ${iconSrc} $out/share/icons/hicolor/48x48/apps/${iconName}.png
      # Alias icône générique fray
      for s in 48x48 128x128 256x256 512x512; do
        cp $out/share/icons/hicolor/$s/apps/${iconName}.png \
           $out/share/icons/hicolor/$s/apps/fray.png
      done

      iconPath="$out/share/icons/hicolor/256x256/apps/${iconName}.png"

      makeWrapper ${pythonEnv}/bin/python3 $out/bin/${iconName} \
        --add-flags "$out/share/fray-apply/fray-apply.py" \
        --set FRAY_APPLY_ICON "$iconPath" \
        --set-default FRAY_ICON "$iconPath" \
        --set-default FRAY_FLAKE ${lib.escapeShellArg flakeDir} \
        --prefix PATH : ${lib.makeBinPath (with pkgs; [ nix nh coreutils ])}

      cat > $out/share/applications/${iconName}.desktop <<'DESKTOP'
[Desktop Entry]
Name=Fray Editor Config
Comment=Éditeur / apply de la config Fray (customConfig)
Exec=fray-apply
Icon=fray-apply
Terminal=false
Type=Application
Categories=System;Settings;Administration;
Keywords=nix;nixos;config;fray;apply;editor;
StartupWMClass=fray-apply
DESKTOP

      runHook postInstall
    '';
  };
in
{
  options.fray.apps.apply = {
    enable = lib.mkEnableOption "Fray Editor Config (éditeur Python / apply customConfig)";
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [ frayApplyPkg ];
  };
}
