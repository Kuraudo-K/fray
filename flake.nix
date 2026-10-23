# Fray - flake NixOS (gaming perso)
# Inputs pinés dans flake.lock ; modules dans customConfig/
{
  description = "Fray - NixOS gaming (GNOME / Plasma)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    nix-flatpak.url = "github:gmodena/nix-flatpak?ref=latest";

    faugus-launcher = {
      url = "git+https://framagit.org/gaming-linux-fr/glf-os/app-glf-os/faugus-launcher.git?ref=main";
      flake = false;
    };

    # Secure Boot optionnel (alternatif Limine SB)
    lanzaboote = {
      url = "github:nix-community/lanzaboote/v1.1.0";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      nix-flatpak,
      faugus-launcher,
      lanzaboote,
      ...
    }@inputs:
    let
      system = "x86_64-linux";
      lib = nixpkgs.lib;

      frayOverlay = final: prev: {
        faugus-launcher = final.callPackage "${faugus-launcher}/default.nix" { };
        # nixpkgs khal 0.14.1 : sortie « man » absente -> casse system-path
        khal = prev.khal.overrideAttrs (old: {
          postInstall = (old.postInstall or "") + ''
            mkdir -p "$man/share/man"
          '';
        });
      };

      mkNixos =
        modules:
        lib.nixosSystem {
          inherit system;
          specialArgs = { inherit self inputs; };
          modules = [
            {
              nixpkgs.overlays = [ frayOverlay ];
              nixpkgs.config.allowUnfree = true;
            }
            nix-flatpak.nixosModules.nix-flatpak
            lanzaboote.nixosModules.lanzaboote
          ]
          ++ modules;
        };
    in
    {
      overlays.default = frayOverlay;
      nixosModules.default = ./customConfig;
      nixosModules.fray = ./customConfig;

      nixosConfigurations = {
        fray-iso = mkNixos [ ./hosts/iso.nix ];
        # Cible Calamares (hardware + calamares-generated présents après install)
        fray = mkNixos [ ./hosts/fray.nix ];
      };

      packages.${system} = {
        iso = self.nixosConfigurations.fray-iso.config.system.build.isoImage;
        default = self.nixosConfigurations.fray-iso.config.system.build.isoImage;
      };
    };
}
