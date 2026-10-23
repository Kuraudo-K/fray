//! Cas d'usage : orchestre les ports. Aucun GTK, aucun détail d'OS.

use std::sync::Arc;

use crate::domain::{short_msg, PowerMode, Settings};
use crate::ports::{
    OpResult, PowerStore, PreferencesStore, SystemGateway, SystemStatus, ThemePort,
};

pub struct UpdateManagerService {
    prefs: Arc<dyn PreferencesStore>,
    power: Arc<dyn PowerStore>,
    system: Arc<dyn SystemGateway>,
    theme: Arc<dyn ThemePort>,
}

impl UpdateManagerService {
    pub fn new(
        prefs: Arc<dyn PreferencesStore>,
        power: Arc<dyn PowerStore>,
        system: Arc<dyn SystemGateway>,
        theme: Arc<dyn ThemePort>,
    ) -> Self {
        Self {
            prefs,
            power,
            system,
            theme,
        }
    }

    pub fn load_settings(&self) -> Settings {
        let mut cfg = self.prefs.load().unwrap_or_default();
        if self.power.exists() {
            cfg.power_mode = self.power.read();
        }
        cfg
    }

    pub fn set_power_mode(&self, mode: PowerMode) -> Result<(), String> {
        self.power.write(mode)
    }

    pub fn apply_settings(&self, settings: &Settings) -> OpResult {
        if let Err(err) = self.power.write(settings.power_mode) {
            return OpResult {
                ok: false,
                detail: err,
            };
        }
        if let Err(err) = self.prefs.save(settings) {
            return OpResult {
                ok: false,
                detail: err,
            };
        }
        self.system.apply_config()
    }

    pub fn apply_status_message(&self, result: &OpResult) -> (String, bool) {
        if result.ok {
            let cfg = self.load_settings();
            let msg = if cfg.auto_upgrade {
                "Config appliquée — auto-màj activée.".to_string()
            } else if cfg.schedule_enable {
                format!(
                    "Config appliquée — planning {} {:02}:{:02}.",
                    cfg.weekday.as_str(),
                    cfg.hour,
                    cfg.minute
                )
            } else {
                "Config appliquée — auto-màj désactivée (prefs: autoUpgrade=false).".to_string()
            };
            (msg, false)
        } else {
            (
                short_msg(false, &result.detail, "", "Échec de l'application"),
                true,
            )
        }
    }

    pub fn update_now(&self, settings: &Settings) -> OpResult {
        if let Err(err) = self.power.write(settings.power_mode) {
            return OpResult {
                ok: false,
                detail: err,
            };
        }
        self.system.run_update()
    }

    pub fn update_status_message(&self, result: &OpResult) -> (String, bool) {
        (
            short_msg(
                result.ok,
                &result.detail,
                "Mise à jour terminée.",
                "Échec de la mise à jour",
            ),
            !result.ok,
        )
    }

    pub fn system_status(&self) -> SystemStatus {
        SystemStatus {
            settings: self.load_settings(),
            auto_timer: self.system.timer_state("fray-auto-update.timer"),
            calendar_timer: self.system.timer_state("fray-auto-update-calendar.timer"),
        }
    }

    pub fn prefers_dark(&self) -> bool {
        self.theme.prefers_dark()
    }
}
