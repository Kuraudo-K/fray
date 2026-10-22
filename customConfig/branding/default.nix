# Branding Fray — logo officiel 10-seal-fray
# Branché : icônes hicolor, GDM, wallpapers GNOME/Plasma, paquet Plymouth
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.branding;

  fray-branding = pkgs.callPackage ./package.nix { };
  plymouth-fray = pkgs.callPackage ./plymouth { };
in
{
  options.fray.branding = {
    enable = lib.mkEnableOption "Fray branding (logo 10 seal, wallpapers, Plymouth theme package)";
  };

  config = lib.mkIf cfg.enable {
    nixpkgs.overlays = [
      (_final: _prev: {
        inherit fray-branding plymouth-fray;
      })
    ];

    environment.systemPackages = [ fray-branding ];

    # Logo GDM (greeter GNOME — aussi avec Plasma sans SDDM)
    services.displayManager.gdm = {
      logo = lib.mkDefault "${fray-branding}/share/fray/logo/10-seal-fray.png";
    };

    # Thème Plymouth Fray (activé via fray.boot.plymouth)
    boot.plymouth = lib.mkIf (config.fray.boot.plymouth.enable or false) {
      theme = lib.mkDefault "fray";
      themePackages = lib.mkDefault [ plymouth-fray ];
    };

    # Breeze / Plasma : logo application Fray disponible comme icône « fray »
    environment.variables.FRAY_BRANDING = "${fray-branding}";
  };
}
