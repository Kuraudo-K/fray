//! CLI - clap uniquement ; délègue à application::SwitchService

use clap::{Parser, Subcommand, ValueEnum};
use fray_de_switch::adapters::{DmrcGreeter, FsProfileStore, JsonStateStore, XdgSessionDetector};
use fray_de_switch::application::SwitchService;
use fray_de_switch::domain::SessionId;
use std::process::ExitCode;

#[derive(Debug, Clone, Copy, ValueEnum)]
enum DeCli {
    Gnome,
    Niri,
    Plasma,
    Mango,
}

impl From<DeCli> for SessionId {
    fn from(d: DeCli) -> Self {
        match d {
            DeCli::Gnome => SessionId::Gnome,
            DeCli::Niri => SessionId::Niri,
            DeCli::Plasma => SessionId::Plasma,
            DeCli::Mango => SessionId::Mango,
        }
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
    List,
    Save {
        #[arg(value_enum)]
        de: Option<DeCli>,
    },
    Restore {
        #[arg(value_enum)]
        de: DeCli,
    },
    Switch {
        #[arg(value_enum)]
        to: DeCli,
    },
    Explain,
}

fn main() -> ExitCode {
    let cli = Cli::parse();
    let detector = XdgSessionDetector;
    let profiles = FsProfileStore;
    let greeter = DmrcGreeter;
    let state = JsonStateStore;
    let svc = SwitchService {
        detector: &detector,
        profiles: &profiles,
        greeter: &greeter,
        state: &state,
    };

    let result = match cli.cmd {
        Commands::List => {
            let info = svc.list();
            println!("DE disponibles / available:");
            for de in SessionId::all() {
                println!("  {:7} - {}", de.as_str(), de.label());
            }
            println!(
                "Session courante / current: {}",
                info.current.map(|d| d.as_str()).unwrap_or("inconnue")
            );
            println!(
                "Préféré greeter / preferred: {}",
                info.preferred.as_deref().unwrap_or("(aucun)")
            );
            println!(
                "Dernier save / last saved: {}",
                info.last_saved.as_deref().unwrap_or("(aucun)")
            );
            println!("Profils : {}", info.profiles_root);
            Ok(())
        }
        Commands::Save { de } => svc.save(de.map(Into::into)).map(|session| {
            eprintln!("[fray-de-switch] profil sauvé : {}", session.as_str());
        }),
        Commands::Restore { de } => svc.restore(de.into()),
        Commands::Switch { to } => {
            let to = SessionId::from(to);
            svc.switch(to).map(|_| {
                eprintln!(
                    "[fray-de-switch] OK -> {}. Déconnecte-toi puis choisis « {} ».",
                    to.label(),
                    to.greeter_id()
                );
            })
        }
        Commands::Explain => {
            print!("{}", svc.explain());
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
