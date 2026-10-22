//! CLI - clap -> application::WallpaperService

use clap::{Parser, Subcommand};
use fray_wallpaper::adapters::{CompositeApplier, EnvDesktopDetector, FsCatalog};
use fray_wallpaper::application::WallpaperService;
use std::process::ExitCode;

#[derive(Parser)]
#[command(
    name = "fray-wallpaper",
    about = "Fonds d'écran Fray (liste / applique selon le DE)"
)]
struct Cli {
    #[command(subcommand)]
    cmd: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Liste les fonds connus
    List,
    /// Liste JSON (GUI)
    ListJson,
    /// Applique un fond (id catalogue ou chemin fichier)
    Set { target: String },
    /// Réapplique le dernier choix ou le fond Fray par défaut
    Auto,
    /// Affiche le DE détecté et le fond actuel
    Current,
    Explain,
}

fn main() -> ExitCode {
    let cli = Cli::parse();
    let catalog = FsCatalog::default();
    let applier = CompositeApplier;
    let desktop = EnvDesktopDetector;
    let svc = WallpaperService {
        catalog: &catalog,
        applier: &applier,
        desktop: &desktop,
    };

    let result = match cli.cmd {
        Commands::List => svc.list_text().map(|t| print!("{t}")),
        Commands::ListJson => svc.list_json().map(|t| println!("{t}")),
        Commands::Set { target } => svc.set(&target),
        Commands::Auto => svc.auto(),
        Commands::Current => svc.current_text().map(|t| print!("{t}")),
        Commands::Explain => {
            print!("{}", svc.explain());
            Ok(())
        }
    };

    match result {
        Ok(()) => ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("[fray-wallpaper] erreur: {e}");
            ExitCode::FAILURE
        }
    }
}
