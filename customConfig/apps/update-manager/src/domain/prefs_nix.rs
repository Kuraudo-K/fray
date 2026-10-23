use std::sync::LazyLock;

use regex::Regex;

use super::model::{PowerMode, Settings, Weekday};

pub fn parse_prefs_nix(text: &str) -> Settings {
    let mut cfg = Settings::default();

    if let Some(value) = first_group(text, r"autoUpgrade\s*=\s*(true|false)\s*;") {
        cfg.auto_upgrade = value == "true";
    }
    if let Some(value) = first_group(text, r"schedule\s*=\s*\{[^}]*?enable\s*=\s*(true|false)\s*;")
    {
        cfg.schedule_enable = value == "true";
    }
    if let Some(value) = first_group(text, r#"weekday\s*=\s*"([A-Za-z]+)"\s*;"#) {
        if let Some(day) = Weekday::parse(&value) {
            cfg.weekday = day;
        }
    }
    if let Some(value) = first_group(text, r"hour\s*=\s*(\d+)\s*;") {
        if let Ok(hour) = value.parse::<i64>() {
            cfg.hour = hour.clamp(0, 23) as u8;
        }
    }
    if let Some(value) = first_group(text, r"minute\s*=\s*(\d+)\s*;") {
        if let Ok(minute) = value.parse::<i64>() {
            cfg.minute = minute.clamp(0, 59) as u8;
        }
    }
    if let Some(value) = first_group(text, r#"powerMode\s*=\s*"(performance|standard|eco)"\s*;"#) {
        cfg.power_mode = PowerMode::parse(&value);
    }
    cfg
}

pub fn render_prefs_nix(cfg: &Settings) -> String {
    let auto = if cfg.auto_upgrade { "true" } else { "false" };
    let sched = if cfg.schedule_enable { "true" } else { "false" };
    format!(
        "{{\n  fray.services.updateManagerGui = {{\n    autoUpgrade = {auto};\n    schedule = {{\n      enable = {sched};\n      weekday = \"{}\";\n      hour = {};\n      minute = {};\n    }};\n    powerMode = \"{}\";\n  }};\n}}\n",
        cfg.weekday.as_str(),
        cfg.hour,
        cfg.minute,
        cfg.power_mode.as_str()
    )
}

fn first_group(text: &str, pattern: &str) -> Option<String> {
    regex_for(pattern)
        .captures(text)
        .and_then(|caps| caps.get(1).map(|m| m.as_str().to_string()))
}

fn regex_for(pattern: &str) -> std::sync::Arc<Regex> {
    static CACHE: LazyLock<
        std::sync::Mutex<std::collections::HashMap<String, std::sync::Arc<Regex>>>,
    > = LazyLock::new(|| std::sync::Mutex::new(std::collections::HashMap::new()));
    let mut cache = CACHE.lock().expect("regex cache");
    cache
        .entry(pattern.to_string())
        .or_insert_with(|| std::sync::Arc::new(Regex::new(pattern).expect("regex valide")))
        .clone()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_prefs_and_maps_performance() {
        let text = r#"{
  fray.services.updateManagerGui = {
    autoUpgrade = false;
    schedule = {
      enable = true;
      weekday = "Mon";
      hour = 99;
      minute = 5;
    };
    powerMode = "performance";
  };
}
"#;
        let cfg = parse_prefs_nix(text);
        assert!(!cfg.auto_upgrade);
        assert!(cfg.schedule_enable);
        assert_eq!(cfg.weekday, Weekday::Mon);
        assert_eq!(cfg.hour, 23);
        assert_eq!(cfg.minute, 5);
        assert_eq!(cfg.power_mode, PowerMode::Standard);
    }

    #[test]
    fn render_roundtrip() {
        let cfg = Settings {
            auto_upgrade: false,
            schedule_enable: false,
            weekday: Weekday::Sat,
            hour: 16,
            minute: 0,
            power_mode: PowerMode::Eco,
        };
        let again = parse_prefs_nix(&render_prefs_nix(&cfg));
        assert_eq!(again, cfg);
    }

    #[test]
    fn ignores_unknown_weekday() {
        let cfg = parse_prefs_nix("weekday = \"Funday\";\n");
        assert_eq!(cfg.weekday, Weekday::Sat);
    }
}
