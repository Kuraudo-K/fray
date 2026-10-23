//! Ports (secondaires + primaire via le service d'application).
//! Le domaine/application dépend de ces traits, jamais des adapters.

use crate::domain::{PowerMode, Settings};

pub trait PreferencesStore: Send + Sync {
    fn load(&self) -> Result<Settings, String>;
    fn save(&self, settings: &Settings) -> Result<(), String>;
}

pub trait PowerStore: Send + Sync {
    fn read(&self) -> PowerMode;
    fn write(&self, mode: PowerMode) -> Result<(), String>;
    fn exists(&self) -> bool;
}

#[derive(Clone, Debug)]
pub struct OpResult {
    pub ok: bool,
    pub detail: String,
}

#[derive(Clone, Debug)]
pub struct SystemStatus {
    pub settings: Settings,
    pub auto_timer: String,
    pub calendar_timer: String,
}

impl SystemStatus {
    pub fn display_lines(&self) -> Vec<String> {
        let auto_pref = if self.settings.auto_upgrade {
            "oui"
        } else {
            "non"
        };
        let sched_pref = if self.settings.schedule_enable {
            "oui"
        } else {
            "non"
        };
        let mut lines = vec![
            format!(
                "Prefs : auto={auto_pref} · planning={sched_pref} · puissance={}",
                self.settings.power_mode.as_str()
            ),
            format!("Timer auto (boot/12h) : {}", self.auto_timer),
            format!("Timer planning : {}", self.calendar_timer),
        ];
        if !self.settings.auto_upgrade && self.auto_timer == "active" {
            lines.push(
                "⚠ Auto désactivée dans prefs mais le timer tourne encore → Appliquer la config"
                    .to_string(),
            );
        }
        lines
    }
}

pub trait SystemGateway: Send + Sync {
    fn apply_config(&self) -> OpResult;
    fn run_update(&self) -> OpResult;
    fn timer_state(&self, unit: &str) -> String;
}

pub trait ThemePort: Send + Sync {
    fn prefers_dark(&self) -> bool;
}

pub trait IconLocator: Send + Sync {
    fn resolve_png(&self) -> Option<std::path::PathBuf>;
}
