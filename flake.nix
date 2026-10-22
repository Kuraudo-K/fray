# Fray — flake NixOS (gaming perso)
# Inputs pinés dans flake.lock ; modules dans customConfig/
{
  description = "Fray — NixOS gaming (GNOME / Niri / Plasma / Mango+DMS)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    nix-flatpak.url = "github:gmodena/nix-flatpak?ref=latest";

    faugus-launcher = {
      url = "git+https://framagit.org/gaming-linux-fr/glf-os/app-glf-os/faugus-launcher.git?ref=main";
      flake = false;
    };

    # MangoWM + DankMaterialShell (4ᵉ DE, reprise mona)
    mango = {
      url = "github:mangowm/mango";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    dms = {
      url = "github:AvengeMedia/DankMaterialShell";
      inputs.nixpkgs.follows = "nixpkgs";
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
      mango,
      dms,
      lanzaboote,
      ...
    }@inputs:
    let
      system = "x86_64-linux";
      lib = nixpkgs.lib;

      frayOverlay = final: prev: {
        faugus-launcher = final.callPackage "${faugus-launcher}/default.nix" { };
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
            mango.nixosModules.mango
            dms.nixosModules.dank-material-shell
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
        fray-vm = mkNixos [ ./hosts/vm.nix ];
        fray-iso = mkNixos [ ./hosts/iso.nix ];
      };

      packages.${system} = {
        vm = self.nixosConfigurations.fray-vm.config.system.build.vm;
        iso = self.nixosConfigurations.fray-iso.config.system.build.isoImage;
        default = self.nixosConfigurations.fray-vm.config.system.build.vm;
      };
    };
}
