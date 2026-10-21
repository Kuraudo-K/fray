# ┌─────────────────────────────────────────────────────────────┐
# │ Fray — flake (inputs pinés → flake.lock)                    │
# │ Apps via nixpkgs + faugus overlay ; modules = customConfig  │
# └─────────────────────────────────────────────────────────────┘
{
  description = "Fray — NixOS gaming perso (GNOME+PaperWM / Niri+Noctalia)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    # Flatpak déclaratif / declarative Flatpak
    nix-flatpak.url = "github:gmodena/nix-flatpak?ref=latest";

    # Faugus (GLF) — absent de nixpkgs / not in nixpkgs
    faugus-launcher = {
      url = "git+https://framagit.org/gaming-linux-fr/glf-os/app-glf-os/faugus-launcher.git?ref=main";
      flake = false;
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      nix-flatpak,
      faugus-launcher,
      ...
    }:
    let
      system = "x86_64-linux";
      lib = nixpkgs.lib;

      # Overlay : seuls les paquets absents de nixpkgs
      # Overlay: only packages missing from nixpkgs
      frayOverlay = final: prev: {
        faugus-launcher = final.callPackage "${faugus-launcher}/default.nix" { };
      };

      mkNixos =
        modules:
        lib.nixosSystem {
          inherit system;
          specialArgs = { inherit self; };
          modules = [
            {
              nixpkgs.overlays = [ frayOverlay ];
              nixpkgs.config.allowUnfree = true;
            }
            nix-flatpak.nixosModules.nix-flatpak
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
