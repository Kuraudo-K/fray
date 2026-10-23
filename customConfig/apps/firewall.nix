# fray-firewall : GUI GTK4/libadwaita (ref nix-firewall-mngt GLF)
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.fray.apps.firewall;
  fray-firewall = pkgs.callPackage ./firewall { };
in
{
  options.fray.apps.firewall = {
    enable = lib.mkEnableOption "Fray Firewall GUI (Rust, ref GLF nix-firewall-mngt)";
  };

  config = lib.mkIf cfg.enable {
    security.polkit.enable = true;

    environment.systemPackages = [ fray-firewall ];

    # Stub vide si absent : l'app ecrit system/firewall-managed.nix
    # et peut injecter l'import dans default.nix.
  };
}
