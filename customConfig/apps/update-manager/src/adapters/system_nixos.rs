use std::env;
use std::path::{Path, PathBuf};
use std::time::Duration;

use crate::adapters::config::AppConfig;
use crate::adapters::process::{self, CaptureError, DeleteOnDrop};
use crate::domain::strip_ansi;
use crate::ports::{OpResult, SystemGateway};

pub struct NixOsSystemGateway {
    demo: bool,
}

impl NixOsSystemGateway {
    pub fn new(config: &AppConfig) -> Self {
        Self { demo: config.demo }
    }
}

impl SystemGateway for NixOsSystemGateway {
    fn apply_config(&self) -> OpResult {
        if self.demo {
            return OpResult {
                ok: true,
                detail: "Mode démo — aucun rebuild système.".to_string(),
            };
        }

        let Some(nh) = resolve_nh() else {
            return OpResult {
                ok: false,
                detail: "nh introuvable.".to_string(),
            };
        };

        let Some(askpass) = make_askpass_script() else {
            return OpResult {
                ok: false,
                detail: "Mot de passe requis pour nh os switch. Installez kdialog (KDE) ou zenity, ou lancez : fray-update".to_string(),
            };
        };
        let _cleanup = DeleteOnDrop(Some(askpass.clone()));

        let mut cmd = std::process::Command::new(nh);
        cmd.args([
            "os",
            "switch",
            "/etc/nixos",
            "-H",
            "fray",
            "--",
            "--accept-flake-config",
        ]);
        apply_tool_env(&mut cmd, Some(&askpass));

        match process::capture(cmd, Duration::from_secs(7200)) {
            Ok(output) if output.status.success() => OpResult {
                ok: true,
                detail: "Configuration appliquée.".to_string(),
            },
            Ok(output) => {
                let stderr = process::lossy(&output.stderr);
                let stdout = process::lossy(&output.stdout);
                let err = strip_ansi(if stderr.trim().is_empty() {
                    stdout.trim()
                } else {
                    stderr.trim()
                });
                if err.is_empty() {
                    OpResult {
                        ok: false,
                        detail: format!("Échec nh (code {}).", output.status.code().unwrap_or(-1)),
                    }
                } else {
                    OpResult {
                        ok: false,
                        detail: err,
                    }
                }
            }
            Err(CaptureError::Timeout) => OpResult {
                ok: false,
                detail: "Délai dépassé pendant le rebuild.".to_string(),
            },
            Err(CaptureError::Spawn(err)) if err.kind() == std::io::ErrorKind::NotFound => {
                OpResult {
                    ok: false,
                    detail: "nh introuvable.".to_string(),
                }
            }
            Err(CaptureError::Spawn(err)) => OpResult {
                ok: false,
                detail: err.to_string(),
            },
        }
    }

    fn run_update(&self) -> OpResult {
        if self.demo {
            return OpResult {
                ok: true,
                detail: "Mode démo — fray-update non lancé.".to_string(),
            };
        }
        let Some(binary) = resolve_update_bin() else {
            return OpResult {
                ok: false,
                detail: "fray-update-powered / fray-update introuvable.".to_string(),
            };
        };

        let askpass = make_askpass_script();
        let _cleanup = DeleteOnDrop(askpass.clone());

        let sudo = PathBuf::from("/run/wrappers/bin/sudo");
        let mut cmd = if sudo.is_file() {
            let mut cmd = std::process::Command::new(sudo);
            cmd.arg("-A").arg(&binary);
            cmd
        } else {
            std::process::Command::new(&binary)
        };
        apply_tool_env(&mut cmd, askpass.as_deref());

        match process::capture(cmd, Duration::from_secs(14400)) {
            Ok(output) => {
                let combined = format!(
                    "{}\n{}",
                    process::lossy(&output.stdout),
                    process::lossy(&output.stderr)
                );
                let out = strip_ansi(combined.trim());
                let code = output.status.code();
                if output.status.success() || code == Some(75) {
                    OpResult {
                        ok: true,
                        detail: if out.is_empty() {
                            "Mise à jour terminée.".to_string()
                        } else {
                            out
                        },
                    }
                } else {
                    OpResult {
                        ok: false,
                        detail: if out.is_empty() {
                            format!("Échec (code {}).", code.unwrap_or(-1))
                        } else {
                            out
                        },
                    }
                }
            }
            Err(CaptureError::Timeout) => OpResult {
                ok: false,
                detail: "Délai dépassé pendant la mise à jour.".to_string(),
            },
            Err(CaptureError::Spawn(err)) if err.kind() == std::io::ErrorKind::NotFound => {
                OpResult {
                    ok: false,
                    detail: "sudo / fray-update introuvable.".to_string(),
                }
            }
            Err(CaptureError::Spawn(err)) => OpResult {
                ok: false,
                detail: err.to_string(),
            },
        }
    }

    fn timer_state(&self, unit: &str) -> String {
        let mut cmd = std::process::Command::new("systemctl");
        cmd.args(["is-active", unit]);
        match process::capture(cmd, Duration::from_secs(3)) {
            Ok(output) => {
                let state = process::lossy(&output.stdout);
                let state = state.trim();
                if state.is_empty() {
                    "inconnu".to_string()
                } else {
                    state.to_string()
                }
            }
            Err(_) => "inconnu".to_string(),
        }
    }
}

fn resolve_nh() -> Option<PathBuf> {
    if let Some(found) = process::which("nh") {
        if found.is_file() {
            return Some(found);
        }
    }
    let fallback = PathBuf::from("/run/current-system/sw/bin/nh");
    fallback.is_file().then_some(fallback)
}

fn resolve_update_bin() -> Option<PathBuf> {
    for name in ["fray-update-powered", "fray-update"] {
        if let Some(found) = process::which(name) {
            return Some(found);
        }
        let candidate = PathBuf::from(format!("/run/current-system/sw/bin/{name}"));
        if candidate.is_file() {
            return Some(candidate);
        }
    }
    None
}

fn apply_tool_env(cmd: &mut std::process::Command, askpass: Option<&Path>) {
    let extra = "/run/wrappers/bin:/run/current-system/sw/bin:/nix/var/nix/profiles/default/bin";
    let old = env::var("PATH").unwrap_or_default();
    cmd.env("PATH", format!("{extra}:{old}"));
    if let Some(askpass) = askpass {
        let askpass = askpass.display().to_string();
        cmd.env("SUDO_ASKPASS", &askpass);
        cmd.env("NH_ASKPASS", &askpass);
        cmd.env("SUDO_ASKPASS_REQUIRE", "force");
    }
}

fn make_askpass_script() -> Option<PathBuf> {
    let desktop = format!(
        "{}{}",
        env::var("XDG_CURRENT_DESKTOP").unwrap_or_default(),
        env::var("DESKTOP_SESSION").unwrap_or_default()
    )
    .to_lowercase();
    let prefer_kde = desktop.contains("kde") || desktop.contains("plasma");
    let tools: &[&str] = if prefer_kde {
        &["kdialog", "zenity"]
    } else {
        &["zenity", "kdialog"]
    };

    let mut candidates: Vec<(&str, PathBuf)> = Vec::new();
    for tool in tools {
        if let Some(found) = process::which(tool) {
            candidates.push((*tool, found));
        }
        for base in ["/run/wrappers/bin", "/run/current-system/sw/bin"] {
            let path = PathBuf::from(base).join(tool);
            if path.is_file() {
                candidates.push((*tool, path));
            }
        }
    }

    let mut seen = std::collections::HashSet::new();
    for (tool, found) in candidates {
        if !seen.insert(found.clone()) {
            continue;
        }
        let cmd_line = if tool == "zenity" {
            format!(
                "{} --password --title=\"Fray\" --text=\"Mot de passe :\"",
                found.display()
            )
        } else {
            format!("{} --password \"Mot de passe :\"", found.display())
        };
        let body = format!("#!/bin/sh\nexec {cmd_line}\n");
        if let Ok(path) = process::write_private_script(&body) {
            return Some(path);
        }
    }
    None
}
