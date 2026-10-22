# Options fray.features.* + catalogue JSON pour outils Fray
{
  config,
  lib,
  pkgs,
  ...
}:

let
  catalog = import ./catalog.nix;

  profileNames = builtins.attrNames catalog.profiles;
  activeGroups = catalog.profiles.${config.fray.profile} or [ ];

  catalogJson = pkgs.writeText "fray-catalog.json" (builtins.toJSON catalog);

  mkGroupOptions =
    groupName: group:
    {
      enable = lib.mkOption {
        type = lib.types.bool;
        default = lib.elem groupName activeGroups;
        defaultText = lib.literalMD "actif si le groupe est dans `fray.profile`";
        description = "Activer le groupe ${group.label.fr or groupName}.";
      };
    }
    // lib.optionalAttrs (group ? apps) {
      apps = lib.mapAttrs (appName: app: {
        enable = lib.mkOption {
          type = lib.types.bool;
          default = config.fray.features.${groupName}.enable;
          defaultText = lib.literalMD "suit `fray.features.${groupName}.enable`";
          description = "Activer ${app.label.fr or appName}.";
        };
      }) group.apps;
    };
in
{
  options.fray.profile = lib.mkOption {
    type = lib.types.enum profileNames;
    default = "full";
    description = ''
      Profil Fray : preset de groupes `fray.features.*`.
      Les modules customConfig restent les vrais interrupteurs (`fray.*.enable`).
    '';
  };

  options.fray.features = lib.mapAttrs mkGroupOptions catalog.groups;

  options.fray.catalog = {
    enable = lib.mkEnableOption "Publier /etc/fray/catalog.json" // {
      default = true;
    };
  };

  config = lib.mkIf config.fray.catalog.enable {
    environment.etc."fray/catalog.json".source = catalogJson;
  };
}
