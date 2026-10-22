# Calamares branding Fray (logo 10) + module nixos Fray
{ ... }:

let
  calamaresFiles = ./calamares;
  logoSvg = ../customConfig/branding/assets/logo/10-seal-fray.svg;
  logoPng = ../customConfig/branding/assets/logo/10-seal-fray.png;
in
{
  nixpkgs.overlays = [
    (_final: prev: {
      calamares-nixos-extensions = prev.calamares-nixos-extensions.overrideAttrs (old: {
        postInstall = (old.postInstall or "") + ''
          mkdir -p \
            $out/etc/calamares/modules \
            $out/lib/calamares/modules/nixos \
            $out/share/calamares/branding/fray

          cp ${calamaresFiles}/modules/nixos/main.py \
            $out/lib/calamares/modules/nixos/main.py
          cp ${calamaresFiles}/config/settings.conf \
            $out/etc/calamares/settings.conf
          cp ${calamaresFiles}/config/modules/*.conf \
            $out/etc/calamares/modules/

          cp ${calamaresFiles}/branding/fray/branding.desc \
            $out/share/calamares/branding/fray/
          cp ${calamaresFiles}/branding/fray/show.qml \
            $out/share/calamares/branding/fray/
          cp ${logoSvg} $out/share/calamares/branding/fray/logo-fray.svg
          cp ${logoPng} $out/share/calamares/branding/fray/logo-fray.png
        '';
      });
    })
  ];

  system.nixos.distroId = "fray";
  system.nixos.distroName = "Fray";
}
