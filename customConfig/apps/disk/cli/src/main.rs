//! CLI - clap -> application::DiskService

use clap::{Parser, Subcommand};
use fray_disk::adapters::{LsblkLister, UdisksMounter, WhichDesktopTool};
use fray_disk::application::DiskService;
use std::path::PathBuf;
use std::process::ExitCode;

#[derive(Parser)]
#[command(
    name = "fray-disk",
    about = "Disques / partitions (lecture + actions sûres)"
)]
struct Cli {
    #[command(subcommand)]
    cmd: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Liste disques et partitions (lsblk)
    List,
    /// Liste JSON (GUI)
    ListJson,
    /// Détail d'un périphérique
    Info { name: String },
    /// Ouvre GNOME Disks ou KDE Partition Manager
    Open,
    /// Monte un bloc via udisksctl (exige --yes)
    Mount {
        device: String,
        #[arg(long)]
        yes: bool,
    },
    /// Démonte via udisksctl (exige --yes)
    Umount {
        target: String,
        #[arg(long)]
        yes: bool,
    },
    /// Affiche un snippet fileSystems Nix
    GenNix {
        /// Inclure /, /boot, /nix
        #[arg(long)]
        system: bool,
    },
    /// Écrit le snippet Nix (exige --yes)
    WriteNix {
        #[arg(long)]
        path: Option<PathBuf>,
        #[arg(long)]
        system: bool,
        #[arg(long)]
        yes: bool,
    },
    Explain,
}

fn main() -> ExitCode {
    let cli = Cli::parse();
    let lister = LsblkLister;
    let mounter = UdisksMounter;
    let desktop = WhichDesktopTool;
    let svc = DiskService {
        lister: &lister,
        mounter: &mounter,
        desktop: &desktop,
    };

    let result = match cli.cmd {
        Commands::List => svc.list_text().map(|t| print!("{t}")),
        Commands::ListJson => svc.list_json().map(|t| println!("{t}")),
        Commands::Info { name } => svc.info(&name).map(|t| print!("{t}")),
        Commands::Open => svc.open_desktop_tool(),
        Commands::Mount { device, yes } => svc.mount(&device, yes),
        Commands::Umount { target, yes } => svc.unmount(&target, yes),
        Commands::GenNix { system } => svc.gen_nix_text(system).map(|t| print!("{t}")),
        Commands::WriteNix { path, system, yes } => {
            let out = path.unwrap_or_else(DiskService::default_nix_out_path);
            svc.write_nix(&out, system, yes).map(|_| {
                eprintln!("[fray-disk] écrit : {}", out.display());
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
            eprintln!("[fray-disk] erreur: {e}");
            ExitCode::FAILURE
        }
    }
}
