use crate::domain::{DiskError, DiskResult};
use crate::ports::DesktopDiskTool;
use std::path::Path;
use std::process::Command;

pub struct WhichDesktopTool;

impl DesktopDiskTool for WhichDesktopTool {
    fn open(&self) -> DiskResult<()> {
        for bin in ["gnome-disks", "partitionmanager", "baobab"] {
            if which(bin) {
                Command::new(bin)
                    .spawn()
                    .map_err(|e| DiskError::Io(e.to_string()))?;
                eprintln!("[fray-disk] lancé : {bin}");
                return Ok(());
            }
        }
        Err(DiskError::NotFound(
            "aucun outil DE trouvé (gnome-disks / partitionmanager)".into(),
        ))
    }
}

fn which(bin: &str) -> bool {
    if let Ok(path) = std::env::var("PATH") {
        for dir in path.split(':') {
            if Path::new(dir).join(bin).is_file() {
                return true;
            }
        }
    }
    false
}
