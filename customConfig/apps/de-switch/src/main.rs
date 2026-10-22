//! fray-de-switch — bascule GNOME / Niri / Plasma avec profils persistants
//! Profiles: ~/.local/share/fray/de-profiles/{gnome,niri,plasma}/

use clap::{Parser, Subcommand, ValueEnum};
use serde::{Deserialize, Serialize};
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::{Command, ExitCode};

#[derive(Debug, Clone, Copy, ValueEnum, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
enum De {
    /// GNOME + PaperWM
    Gnome,
    /// Niri + Noctalia
    Niri,
    /// KDE Plasma 6
    Plasma,
}

impl De {
    fn as_str(self) -> &'static str {
        match self {
            De::Gnome => "gnome",
            De::Niri => "niri",
            De::Plasma => "plasma",
        }
    }

    fn session_id(self) -> &'static str {
        match self {
            De::Gnome => "gnome",
            De::Niri => "niri",
            De::Plasma => "plasma",
        }
    }

    fn label(self) -> &'static str {
        match self {
            De::Gnome => "GNOME + PaperWM",
            De::Niri => "Niri + Noctalia",
            De::Plasma => "KDE Plasma 6",
        }
    }

    fn all() -> [De; 3] {
        [De::Gnome, De::Niri, De::Plasma]
    }
}

#[derive(Parser)]
#[command(
    name = "fray-de-switch",
    about = "Bascule de bureau avec persistance des customs / DE switch + profile persist"
)]
struct Cli {
    #[command(subcommand)]
    cmd: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Liste les DE et le profil actif
    List,
    /// Sauve le profil du DE courant (ou indiqué)
    Save {
        #[arg(value_enum)]
        de: Option<De>,
    },
    /// Restaure un profil DE vers les chemins live
    Restore {
        #[arg(value_enum)]
        de: De,
    },
    /// Sauve le DE actuel, restaure la cible, fixe la session greeter
    Switch {
        #[arg(value_enum)]
        to: De,
    },
    /// Affiche le mécanisme de persistance
    Explain,
}

#[derive(Serialize, Deserialize, Default)]
struct State {
    preferred: Option<String>,
    last_saved: Option<String>,
}

fn data_root() -> PathBuf {
    dirs::data_local_dir()
        .unwrap_or_else(|| PathBuf::from(".").join(".local/share"))
        .join("fray")
}

fn profiles_root() -> PathBuf {
    data_root().join("de-profiles")
}

fn state_path() -> PathBuf {
    data_root().join("de-state.json")
}

fn load_state() -> State {
    let p = state_path();
    fs::read_to_string(&p)
        .ok()
        .and_then(|s| serde_json::from_str(&s).ok())
        .unwrap_or_default()
}

fn save_state(st: &State) -> io::Result<()> {
    fs::create_dir_all(data_root())?;
    fs::write(state_path(), serde_json::to_string_pretty(st).unwrap())?;
    Ok(())
}

fn detect_de() -> Option<De> {
    let desk = std::env::var("XDG_CURRENT_DESKTOP").unwrap_or_default();
    let desk = desk.to_uppercase();
    if desk.contains("GNOME") {
        Some(De::Gnome)
    } else if desk.contains("NIRI") {
        Some(De::Niri)
    } else if desk.contains("KDE") || desk.contains("PLASMA") {
        Some(De::Plasma)
    } else {
        None
    }
}

fn home() -> PathBuf {
    dirs::home_dir().expect("HOME")
}

/// Chemins live à persister par DE / live paths to persist per DE
fn live_paths(de: De) -> Vec<(PathBuf, &'static str)> {
    let h = home();
    match de {
        De::Gnome => vec![
            (h.join(".config/dconf"), "dconf"),
            (h.join(".config/paperwm"), "paperwm"),
            (
                h.join(".local/share/gnome-shell/extensions"),
                "gnome-shell-extensions",
            ),
        ],
        De::Niri => vec![
            (h.join(".config/niri"), "niri"),
            (h.join(".config/noctalia"), "noctalia"),
        ],
        De::Plasma => vec![
            // Bureau / shell
            (h.join(".config/plasma-org.kde.plasma.desktop-appletsrc"), "plasma-appletsrc"),
            (h.join(".config/plasmashellrc"), "plasmashellrc"),
            (h.join(".config/plasmarc"), "plasmarc"),
            (h.join(".config/plasmawindowedrc"), "plasmawindowedrc"),
            // Fenêtre / raccourcis
            (h.join(".config/kwinrc"), "kwinrc"),
            (h.join(".config/kwinrulesrc"), "kwinrulesrc"),
            (h.join(".config/kglobalshortcutsrc"), "kglobalshortcutsrc"),
            (h.join(".config/kdeglobals"), "kdeglobals"),
            (h.join(".config/kdedefaults"), "kdedefaults"),
            // Apps courantes
            (h.join(".config/dolphinrc"), "dolphinrc"),
            (h.join(".config/konsolerc"), "konsolerc"),
            // Thèmes / layouts locaux
            (h.join(".local/share/plasma"), "share-plasma"),
            (h.join(".local/share/kwin"), "share-kwin"),
            (h.join(".local/share/konsole"), "share-konsole"),
        ],
    }
}

fn copy_tree(src: &Path, dst: &Path) -> io::Result<()> {
    if !src.exists() {
        return Ok(());
    }
    if src.is_file() {
        if let Some(parent) = dst.parent() {
            fs::create_dir_all(parent)?;
        }
        fs::copy(src, dst)?;
        return Ok(());
    }
    fs::create_dir_all(dst)?;
    for entry in fs::read_dir(src)? {
        let entry = entry?;
        let ty = entry.file_type()?;
        let to = dst.join(entry.file_name());
        if ty.is_dir() {
            copy_tree(&entry.path(), &to)?;
        } else if ty.is_file() {
            fs::copy(entry.path(), &to)?;
        }
    }
    Ok(())
}

fn remove_tree(path: &Path) -> io::Result<()> {
    if path.is_dir() {
        fs::remove_dir_all(path)?;
    } else if path.is_file() {
        fs::remove_file(path)?;
    }
    Ok(())
}

fn profile_dir(de: De) -> PathBuf {
    profiles_root().join(de.as_str())
}

fn save_profile(de: De) -> io::Result<()> {
    let dest_root = profile_dir(de);
    fs::create_dir_all(&dest_root)?;
    for (live, name) in live_paths(de) {
        let dest = dest_root.join(name);
        let _ = remove_tree(&dest);
        copy_tree(&live, &dest)?;
        eprintln!(
            "[fray-de-switch] sauvé {} → {}",
            live.display(),
            dest.display()
        );
    }
    let mut st = load_state();
    st.last_saved = Some(de.as_str().into());
    save_state(&st)?;
    Ok(())
}

fn restore_profile(de: De) -> io::Result<()> {
    let src_root = profile_dir(de);
    if !src_root.exists() {
        eprintln!(
            "[fray-de-switch] aucun profil pour {} (première utilisation OK)",
            de.label()
        );
        return Ok(());
    }
    for (live, name) in live_paths(de) {
        let src = src_root.join(name);
        if !src.exists() {
            continue;
        }
        if let Some(parent) = live.parent() {
            fs::create_dir_all(parent)?;
        }
        let _ = remove_tree(&live);
        copy_tree(&src, &live)?;
        eprintln!(
            "[fray-de-switch] restauré {} ← {}",
            live.display(),
            src.display()
        );
    }
    Ok(())
}

fn set_preferred_session(de: De) -> io::Result<()> {
    let mut st = load_state();
    st.preferred = Some(de.as_str().into());
    save_state(&st)?;

    let dmrc = home().join(".dmrc");
    let body = format!("[Desktop]\nSession={}\n", de.session_id());
    fs::write(&dmrc, body)?;
    eprintln!(
        "[fray-de-switch] session greeter → {} ({})",
        de.session_id(),
        dmrc.display()
    );

    if let Ok(user) = std::env::var("USER") {
        let as_path = PathBuf::from(format!("/var/lib/AccountsService/users/{user}"));
        if as_path.exists() && Command::new("pkexec").arg("true").status().is_ok() {
            let _ = Command::new("pkexec")
                .args([
                    "busctl",
                    "call",
                    "org.freedesktop.Accounts",
                    &format!("/org/freedesktop/Accounts/User{}", nix_uid()),
                    "org.freedesktop.Accounts.User",
                    "SetXSession",
                    "s",
                    de.session_id(),
                ])
                .status();
        }
    }
    Ok(())
}

fn nix_uid() -> u32 {
    Command::new("id")
        .arg("-u")
        .output()
        .ok()
        .and_then(|o| String::from_utf8(o.stdout).ok())
        .and_then(|s| s.trim().parse().ok())
        .unwrap_or(1000)
}

fn run() -> io::Result<()> {
    let cli = Cli::parse();
    match cli.cmd {
        Commands::List => {
            let st = load_state();
            let current = detect_de();
            println!("DE disponibles / available:");
            for de in De::all() {
                println!("  {:7} — {}", de.as_str(), de.label());
            }
            println!(
                "Session courante / current: {}",
                current.map(|d| d.as_str()).unwrap_or("inconnue")
            );
            println!(
                "Préféré greeter / preferred: {}",
                st.preferred.as_deref().unwrap_or("(aucun)")
            );
            println!(
                "Dernier save / last saved: {}",
                st.last_saved.as_deref().unwrap_or("(aucun)")
            );
            println!("Profils : {}", profiles_root().display());
            Ok(())
        }
        Commands::Save { de } => {
            let de = de.or_else(detect_de).ok_or_else(|| {
                io::Error::new(
                    io::ErrorKind::Other,
                    "DE inconnu — passe gnome|niri|plasma",
                )
            })?;
            save_profile(de)
        }
        Commands::Restore { de } => restore_profile(de),
        Commands::Switch { to } => {
            if let Some(cur) = detect_de() {
                if cur != to {
                    save_profile(cur)?;
                }
            }
            restore_profile(to)?;
            set_preferred_session(to)?;
            eprintln!(
                "[fray-de-switch] OK → {}. Déconnecte-toi puis choisis « {} ».",
                to.label(),
                to.session_id()
            );
            Ok(())
        }
        Commands::Explain => {
            println!(
                r#"Mécanisme / Mechanism
=====================
Profils : ~/.local/share/fray/de-profiles/{{gnome,niri,plasma}}/

  gnome  → dconf, paperwm, extensions gnome-shell
  niri   → ~/.config/niri, ~/.config/noctalia
  plasma → plasma*/kwin*/kdeglobals, dolphin/konsole,
           ~/.local/share/{{plasma,kwin,konsole}}

switch <de> :
  1. sauve le DE courant
  2. restaure le profil cible
  3. écrit ~/.dmrc (Session=gnome|niri|plasma)

Au login GDM, choisir la session. Chaque DE garde ses customs.
"#
            );
            Ok(())
        }
    }
}

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("[fray-de-switch] erreur: {e}");
            ExitCode::FAILURE
        }
    }
}
