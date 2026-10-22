# Sécurité de base (firewall + blacklist modules kernel à risque)
# Ne bloque pas les user namespaces (flatpak / Steam / bwrap en ont besoin)
{
  config,
  lib,
  ...
}:

let
  cfg = config.fray.system.security;
in
{
  options.fray.system.security = {
    enable = lib.mkEnableOption "Base firewall and kernel module blacklists";
    blacklistVpnEsp = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Blacklist esp4/esp6/rxrpc kernel modules (disable only if you need IPsec/AFS)";
    };
    blacklistAlgifAead = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Blacklist algif_aead (AF_ALG) to shrink kernel crypto attack surface";
    };
  };

  config = lib.mkIf cfg.enable {
    networking.firewall.enable = lib.mkDefault true;

    boot.blacklistedKernelModules =
      lib.optionals cfg.blacklistVpnEsp [
        "esp4"
        "esp6"
        "rxrpc"
      ]
      ++ lib.optionals cfg.blacklistAlgifAead [ "algif_aead" ];
  };
}
