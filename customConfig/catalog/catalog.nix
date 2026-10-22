# Catalogue Fray — modules / options (données pures, pas de pkgs).
# Alimente fray.features.* et /etc/fray/catalog.json.
# Slot 8bitdo préparé (module pas encore câblé).

{
  groups = {
    gaming = {
      label = {
        fr = "Jeux";
        en = "Gaming";
      };
      description = {
        fr = "Lanceurs, Proton/umu, overlays et GameMode.";
        en = "Launchers, Proton/umu, overlays and GameMode.";
      };
      apps = {
        steam = {
          label = {
            fr = "Steam";
            en = "Steam";
          };
        };
        lutris = {
          label = {
            fr = "Lutris";
            en = "Lutris";
          };
        };
        heroic = {
          label = {
            fr = "Heroic Games Launcher";
            en = "Heroic Games Launcher";
          };
        };
        faugus = {
          label = {
            fr = "Faugus Launcher";
            en = "Faugus Launcher";
          };
        };
        umu = {
          label = {
            fr = "umu-launcher";
            en = "umu-launcher";
          };
        };
        proton = {
          label = {
            fr = "Proton-GE";
            en = "Proton-GE";
          };
        };
        gamemode = {
          label = {
            fr = "GameMode";
            en = "GameMode";
          };
        };
        gamescope = {
          label = {
            fr = "Gamescope";
            en = "Gamescope";
          };
        };
        mangohud = {
          label = {
            fr = "MangoHud";
            en = "MangoHud";
          };
        };
        # Slot catalogue — module Nix pas encore dans Fray
        "8bitdo" = {
          label = {
            fr = "8BitDo (Wine) — bientôt";
            en = "8BitDo (Wine) — later";
          };
        };
      };
    };

    communication = {
      label = {
        fr = "Communication";
        en = "Communication";
      };
      description = {
        fr = "Messagerie (Discord Flatpak, Matrix).";
        en = "Messaging (Discord Flatpak, Matrix).";
      };
      apps = {
        discord = {
          label = {
            fr = "Discord";
            en = "Discord";
          };
        };
        matrix = {
          label = {
            fr = "Element (Matrix)";
            en = "Element (Matrix)";
          };
        };
      };
    };

    media = {
      label = {
        fr = "Multimédia";
        en = "Media";
      };
      description = {
        fr = "Capture et outils média.";
        en = "Capture and media tools.";
      };
      apps = {
        obs = {
          label = {
            fr = "OBS Studio";
            en = "OBS Studio";
          };
        };
      };
    };

    apps = {
      label = {
        fr = "Applications";
        en = "Apps";
      };
      description = {
        fr = "Navigateur, terminal, base, Flatpak, disque.";
        en = "Browser, terminal, base apps, Flatpak, disk tool.";
      };
      apps = {
        firefox = {
          label = {
            fr = "Firefox";
            en = "Firefox";
          };
        };
        terminal = {
          label = {
            fr = "Terminal (kitty)";
            en = "Terminal (kitty)";
          };
        };
        base = {
          label = {
            fr = "Apps de base";
            en = "Base apps";
          };
        };
        flatpak = {
          label = {
            fr = "Flatpak / Flathub";
            en = "Flatpak / Flathub";
          };
        };
        disk = {
          label = {
            fr = "fray-disk";
            en = "fray-disk";
          };
        };
        apply = {
          label = {
            fr = "Fray Apply (éditeur)";
            en = "Fray Apply (editor)";
          };
        };
      };
    };

    system = {
      label = {
        fr = "Système";
        en = "System";
      };
      description = {
        fr = "nh, aliases, sécu, audio, firmware, updates.";
        en = "nh, aliases, security, audio, firmware, updates.";
      };
      apps = {
        nh = {
          label = {
            fr = "nh + aliases fray-*";
            en = "nh + fray-* aliases";
          };
        };
        aliases = {
          label = {
            fr = "Aliases shell";
            en = "Shell aliases";
          };
        };
        security = {
          label = {
            fr = "Sécurité de base";
            en = "Base security";
          };
        };
        audio = {
          label = {
            fr = "PipeWire / RNNoise";
            en = "PipeWire / RNNoise";
          };
        };
        update-manager = {
          label = {
            fr = "fray-update CLI";
            en = "fray-update CLI";
          };
        };
        auto-update = {
          label = {
            fr = "Timer auto-update";
            en = "Auto-update timer";
          };
        };
      };
    };

    hardware = {
      label = {
        fr = "Matériel";
        en = "Hardware";
      };
      description = {
        fr = "GPU AMD et réglages noyau gaming.";
        en = "AMD GPU and gaming kernel tweaks.";
      };
      apps = {
        amd = {
          label = {
            fr = "AMD graphics";
            en = "AMD graphics";
          };
        };
        kernel-gaming = {
          label = {
            fr = "Kernel gaming";
            en = "Gaming kernel";
          };
        };
      };
    };
  };

  # Quatre sessions Fray
  desktops = {
    gnome = {
      label = {
        fr = "GNOME + PaperWM";
        en = "GNOME + PaperWM";
      };
    };
    niri = {
      label = {
        fr = "Niri + Noctalia";
        en = "Niri + Noctalia";
      };
    };
    plasma = {
      label = {
        fr = "KDE Plasma 6";
        en = "KDE Plasma 6";
      };
    };
    mango = {
      label = {
        fr = "MangoWM + DankMaterialShell";
        en = "MangoWM + DankMaterialShell";
      };
    };
  };

  profiles = {
    mini = [ ];
    gaming = [
      "gaming"
      "communication"
      "apps"
      "system"
      "hardware"
    ];
    full = [
      "gaming"
      "communication"
      "media"
      "apps"
      "system"
      "hardware"
    ];
  };
}
