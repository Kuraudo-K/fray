use std::fs;
use std::path::PathBuf;

use crate::adapters::config::AppConfig;
use crate::adapters::prefs_fs::write_bytes;
use crate::domain::PowerMode;
use crate::ports::PowerStore;

pub struct FsPowerStore {
    path: PathBuf,
    demo: bool,
}

impl FsPowerStore {
    pub fn new(config: &AppConfig) -> Self {
        Self {
            path: config.power_file.clone(),
            demo: config.demo,
        }
    }
}

impl PowerStore for FsPowerStore {
    fn read(&self) -> PowerMode {
        match fs::read_to_string(&self.path) {
            Ok(text) => PowerMode::parse(text.trim()),
            Err(_) => PowerMode::default(),
        }
    }

    fn write(&self, mode: PowerMode) -> Result<(), String> {
        write_bytes(self.demo, &self.path, format!("{}\n", mode.as_str()).as_bytes())
    }

    fn exists(&self) -> bool {
        self.path.exists()
    }
}
