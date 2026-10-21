//! Fray DE switcher — GNOME+PaperWM ↔ Niri+Noctalia
//! Persiste les customs par DE sous ~/.local/share/fray/de-profiles/
//! Persists per-DE customs under ~/.local/share/fray/de-profiles/

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
}

impl De {
    fn as_str(self) -> &'static str {
        match self {
            De::Gnome => "gnome",
            De::Niri => "niri",
        }
    }

    fn session_id(self) -> &'static str {
        match self {
            De::Gnome => "gnome",
            De::Niri => "niri",
        }
    }

    fn label(self) -> &'static str {
        match self {
            De::Gnome => "GNOME + PaperWM",
            De::Niri => "Niri + Noctalia",
        }
    }
}

#[derive(Parser)]
#[command(
    name = "fray-de-switch",
    about = "Fray — bascule DE avec persistance des customs / DE switch + profile persist"
)]
struct Cli {
    #[command(subcommand)]
    cmd: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Liste les DE et le profil actif / list DEs and active profile
    List,
    /// Sauve le profil du DE courant (ou indiqué) / save current (or given) DE profile
    Save {
        #[arg(value_enum)]
        de: Option<De>,
    },
    /// Restaure un profil DE vers les chemins live / restore a DE profile to live paths
    Restore {
        #[arg(value_enum)]
        de: De,
    },
    /// Sauve le DE actuel, restaure la cible, fixe la session greeter
    /// Save current, restore target, set greeter session
    Switch {
        #[arg(value_enum)]
        to: De,
    },
    /// Affiche le mécanisme de persistance / show persistence mechanism
    Explain,
}

#[derive(Serialize, Deserialize, Default)]
struct State {
    /// Dernier DE choisi pour le greeter / last DE chosen for greeter
    preferred: Option<String>,
    /// Dernier DE dont le profil a été sauvé / last DE whose profile was saved
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
            (h.join(".local/share/gnome-shell/extensions"), "gnome-shell-extensions"),
        ],
        De::Niri => vec![
            (h.join(".config/niri"), "niri"),
            (h.join(".config/noctalia"), "noctalia"),
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
        eprintln!("[fray-de-switch] sauvé {} → {}", live.display(), dest.display());
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
        eprintln!("[fray-de-switch] restauré {} ← {}", live.display(), src.display());
    }
    Ok(())
}

fn set_preferred_session(de: De) -> io::Result<()> {
    let mut st = load_state();
    st.preferred = Some(de.as_str().into());
    save_state(&st)?;

    // ~/.dmrc pour GDM / LightDM legacy
    let dmrc = home().join(".dmrc");
    let body = format!(
        "[Desktop]\nSession={}\n",
        de.session_id()
    );
    fs::write(&dmrc, body)?;
    eprintln!(
        "[fray-de-switch] session greeter → {} ({})",
        de.session_id(),
        dmrc.display()
    );

    // AccountsService si présent
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

fn main() -> ExitCode {
    let cli = Cli::parse();
    let result = match cli.cmd {
        Commands::List => {
            let st = load_state();
            let current = detect_de();
            println!("DE disponibles / available:");
            println!("  gnome  — {}", De::Gnome.label());
            println!("  niri   — {}", De::Niri.label());
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
                io::Error::new(io::ErrorKind::Other, "DE inconnu — passe gnome|niri")
            })?;
            save_profile(de)
        }
        Commands::Restore { de } => restore_profile(de),
        Commands::Switch { to } => (|| -> io::Result<()> {
            if let Some(cur) = detect_de() {
                if cur != to {
                    save_profile(cur)?;
                }
            }
            restore_profile(to)?;
            set_preferred_session(to)?;
            eprintln!(
                "[fray-de-switch] OK → {}. Déconnecte-toi puis choisis la session « {} ».",
                to.label(),
                to.session_id()
            );
            eprintln!(
                "[fray-de-switch] Done → {}. Log out, then pick session « {} ».",
                to.label(),
                to.session_id()
            );
            Ok(())
        })(),
        Commands::Explain => {
            println!(
                r#"Mécanisme / Mechanism
=====================
Profils : ~/.local/share/fray/de-profiles/{{gnome,niri}}/
  gnome → dconf, paperwm, gnome-shell extensions
  niri  → ~/.config/niri, ~/.config/noctalia

switch <de> :
  1. sauve le DE courant
  2. restaure le profil cible
  3. écrit ~/.dmrc (Session=gnome|niri)

Au prochain login GDM, choisir la session. Les customs de chaque DE
restent isolées et sont rechargées à chaque switch.
"#
            );
            Ok(())
        }
    };

    match result {
        Ok(()) => ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("[fray-de-switch] erreur: {e}");
            ExitCode::FAILURE
        }
    }
}
