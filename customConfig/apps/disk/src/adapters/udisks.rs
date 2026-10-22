use crate::domain::{DiskError, DiskResult};
use crate::ports::Mounter;
use std::process::Command;

pub struct UdisksMounter;

fn run(cmd: &str, args: &[&str]) -> DiskResult<()> {
    let out = Command::new(cmd)
        .args(args)
        .output()
        .map_err(|e| DiskError::Io(format!("{cmd}: {e}")))?;
    if out.status.success() {
        let stdout = String::from_utf8_lossy(&out.stdout);
        if !stdout.trim().is_empty() {
            eprintln!("[fray-disk] {}", stdout.trim());
        }
        Ok(())
    } else {
        Err(DiskError::Io(format!(
            "{cmd} {}: {}",
            out.status,
            String::from_utf8_lossy(&out.stderr).trim()
        )))
    }
}

impl Mounter for UdisksMounter {
    fn mount(&self, source: &str) -> DiskResult<()> {
        run("udisksctl", &["mount", "-b", source])
    }

    fn unmount(&self, target: &str) -> DiskResult<()> {
        if target.starts_with("/dev/") {
            run("udisksctl", &["unmount", "-b", target])
        } else {
            run("udisksctl", &["unmount", "-p", target])
        }
    }
}
