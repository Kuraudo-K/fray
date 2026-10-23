# Genere / edite par Fray Firewall - ne pas editer a la main si tu uses l'app
{ lib, config, pkgs, ... }:

{
  networking.firewall = {
    enable = true;
    allowedTCPPorts = [ ];
    allowedUDPPorts = [ ];
    allowedTCPPortRanges = [ ];
    allowedUDPPortRanges = [ ];
  };
}
