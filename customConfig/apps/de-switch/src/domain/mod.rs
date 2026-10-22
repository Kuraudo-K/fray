//! Domaine : sessions et chemins de profil — zéro I/O

use std::path::PathBuf;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SessionId {
    Gnome,
    Niri,
    Plasma,
}

impl SessionId {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Gnome => "gnome",
            Self::Niri => "niri",
            Self::Plasma => "plasma",
        }
    }

    /// Identifiant greeter (GDM) / greeter session id
    pub fn greeter_id(self) -> &'static str {
        self.as_str()
    }

    pub fn label(self) -> &'static str {
        match self {
            Self::Gnome => "GNOME + PaperWM",
            Self::Niri => "Niri + Noctalia",
            Self::Plasma => "KDE Plasma 6",
        }
    }

    pub fn all() -> [SessionId; 3] {
        [Self::Gnome, Self::Niri, Self::Plasma]
    }

    pub fn parse(s: &str) -> Option<SessionId> {
        match s.trim().to_lowercase().as_str() {
            "gnome" => Some(Self::Gnome),
            "niri" => Some(Self::Niri),
            "plasma" => Some(Self::Plasma),
            _ => None,
        }
    }

    /// Détecte depuis XDG_CURRENT_DESKTOP (logique pure)
    pub fn from_xdg_desktop(desktop: &str) -> Option<SessionId> {
        let d = desktop.to_uppercase();
        if d.contains("GNOME") {
            Some(Self::Gnome)
        } else if d.contains("NIRI") {
            Some(Self::Niri)
        } else if d.contains("KDE") || d.contains("PLASMA") {
            Some(Self::Plasma)
        } else {
            None
        }
    }
}

/// Relatif live path → nom dans le profil stocké
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProfileEntry {
    pub relative_live: &'static str,
    pub store_name: &'static str,
}

impl SessionId {
    pub fn profile_entries(self) -> &'static [ProfileEntry] {
        match self {
            Self::Gnome => &[
                ProfileEntry {
                    relative_live: ".config/dconf",
                    store_name: "dconf",
                },
                ProfileEntry {
                    relative_live: ".config/paperwm",
                    store_name: "paperwm",
                },
                ProfileEntry {
                    relative_live: ".local/share/gnome-shell/extensions",
                    store_name: "gnome-shell-extensions",
                },
            ],
            Self::Niri => &[
                ProfileEntry {
                    relative_live: ".config/niri",
                    store_name: "niri",
                },
                ProfileEntry {
                    relative_live: ".config/noctalia",
                    store_name: "noctalia",
                },
            ],
            Self::Plasma => &[
                ProfileEntry {
                    relative_live: ".config/plasma-org.kde.plasma.desktop-appletsrc",
                    store_name: "plasma-appletsrc",
                },
                ProfileEntry {
                    relative_live: ".config/plasmashellrc",
                    store_name: "plasmashellrc",
                },
                ProfileEntry {
                    relative_live: ".config/plasmarc",
                    store_name: "plasmarc",
                },
                ProfileEntry {
                    relative_live: ".config/plasmawindowedrc",
                    store_name: "plasmawindowedrc",
                },
                ProfileEntry {
                    relative_live: ".config/kwinrc",
                    store_name: "kwinrc",
                },
                ProfileEntry {
                    relative_live: ".config/kwinrulesrc",
                    store_name: "kwinrulesrc",
                },
                ProfileEntry {
                    relative_live: ".config/kglobalshortcutsrc",
                    store_name: "kglobalshortcutsrc",
                },
                ProfileEntry {
                    relative_live: ".config/kdeglobals",
                    store_name: "kdeglobals",
                },
                ProfileEntry {
                    relative_live: ".config/kdedefaults",
                    store_name: "kdedefaults",
                },
                ProfileEntry {
                    relative_live: ".config/dolphinrc",
                    store_name: "dolphinrc",
                },
                ProfileEntry {
                    relative_live: ".config/konsolerc",
                    store_name: "konsolerc",
                },
                ProfileEntry {
                    relative_live: ".local/share/plasma",
                    store_name: "share-plasma",
                },
                ProfileEntry {
                    relative_live: ".local/share/kwin",
                    store_name: "share-kwin",
                },
                ProfileEntry {
                    relative_live: ".local/share/konsole",
                    store_name: "share-konsole",
                },
            ],
        }
    }

    pub fn live_path(self, home: &std::path::Path, entry: &ProfileEntry) -> PathBuf {
        home.join(entry.relative_live)
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SwitchError {
    UnknownSession(String),
    Io(String),
}

impl std::fmt::Display for SwitchError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::UnknownSession(s) => write!(f, "DE inconnu: {s} (gnome|niri|plasma)"),
            Self::Io(s) => write!(f, "{s}"),
        }
    }
}

impl std::error::Error for SwitchError {}

pub type SwitchResult<T> = Result<T, SwitchError>;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_sessions() {
        assert_eq!(SessionId::parse("gnome"), Some(SessionId::Gnome));
        assert_eq!(SessionId::parse("PLASMA"), Some(SessionId::Plasma));
        assert_eq!(SessionId::parse("nope"), None);
    }

    #[test]
    fn detect_from_xdg() {
        assert_eq!(
            SessionId::from_xdg_desktop("GNOME:GNOME-Classic"),
            Some(SessionId::Gnome)
        );
        assert_eq!(SessionId::from_xdg_desktop("niri"), Some(SessionId::Niri));
        assert_eq!(
            SessionId::from_xdg_desktop("KDE"),
            Some(SessionId::Plasma)
        );
    }

    #[test]
    fn gnome_has_paperwm_entry() {
        let names: Vec<_> = SessionId::Gnome
            .profile_entries()
            .iter()
            .map(|e| e.store_name)
            .collect();
        assert!(names.contains(&"paperwm"));
    }
}
