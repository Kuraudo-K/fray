use std::fs;
use std::io::ErrorKind;
use std::path::PathBuf;

use crate::adapters::config::AppConfig;
use crate::adapters::process;
use crate::domain::{parse_prefs_nix, render_prefs_nix, Settings};
use crate::ports::PreferencesStore;

pub struct FsPreferencesStore {
    path: PathBuf,
    demo: bool,
}

impl FsPreferencesStore {
    pub fn new(config: &AppConfig) -> Self {
        Self {
            path: config.prefs_file.clone(),
            demo: config.demo,
        }
    }
}

impl PreferencesStore for FsPreferencesStore {
    fn load(&self) -> Result<Settings, String> {
        if !self.path.is_file() {
            return Ok(Settings::default());
        }
        let bytes = fs::read(&self.path).map_err(|err| err.to_string())?;
        Ok(parse_prefs_nix(&String::from_utf8_lossy(&bytes)))
    }

    fn save(&self, settings: &Settings) -> Result<(), String> {
        write_bytes(self.demo, &self.path, render_prefs_nix(settings).as_bytes())
    }
}

pub(crate) fn write_bytes(demo: bool, path: &std::path::Path, data: &[u8]) -> Result<(), String> {
    if demo {
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).map_err(|err| err.to_string())?;
        }
        return fs::write(path, data).map_err(|err| err.to_string());
    }
    match fs::write(path, data) {
        Ok(()) => Ok(()),
        Err(err) if err.kind() == ErrorKind::PermissionDenied => process::pkexec_write(path, data),
        Err(err) => Err(err.to_string()),
    }
}
