//! Cas d'usage

use crate::domain::{
    assert_safe_target, find_by_name, format_row, generate_nix_filesystems, BlockDevice, DiskError,
    DiskResult,
};
use crate::ports::{BlockLister, DesktopDiskTool, Mounter};
use std::fs;
use std::path::Path;

pub struct DiskService<'a> {
    pub lister: &'a dyn BlockLister,
    pub mounter: &'a dyn Mounter,
    pub desktop: &'a dyn DesktopDiskTool,
}

impl<'a> DiskService<'a> {
    pub fn list(&self) -> DiskResult<Vec<BlockDevice>> {
        self.lister.list()
    }

    pub fn list_text(&self) -> DiskResult<String> {
        let devices = self.list()?;
        let mut out = String::from("NAME         SIZE      FSTYPE    MOUNTPOINT\n");
        for d in &devices {
            out.push_str(&format_row(d, 0));
            out.push('\n');
            for c in &d.children {
                out.push_str(&format_row(c, 1));
                out.push('\n');
                for gc in &c.children {
                    out.push_str(&format_row(gc, 2));
                    out.push('\n');
                }
            }
        }
        Ok(out)
    }

    pub fn info(&self, name: &str) -> DiskResult<String> {
        let devices = self.list()?;
        let d = find_by_name(&devices, name)
            .ok_or_else(|| DiskError::NotFound(format!("introuvable : {name}")))?;
        Ok(format!(
            "name: {}\npath: {}\nkind: {}\nsize: {}\nfstype: {}\nmount: {}\nlabel: {}\nchildren: {}\n",
            d.name,
            d.path,
            d.kind.as_str(),
            d.size,
            d.fstype.as_deref().unwrap_or("-"),
            d.mountpoint.as_deref().unwrap_or("-"),
            d.label.as_deref().unwrap_or("-"),
            d.children.len()
        ))
    }

    pub fn open_desktop_tool(&self) -> DiskResult<()> {
        self.desktop.open()
    }

    /// Montage via udisks - confirmation côté CLI (flag --yes)
    pub fn mount(&self, source: &str, confirmed: bool) -> DiskResult<()> {
        if !confirmed {
            return Err(DiskError::Refused(
                "montage refusé : passe --yes pour confirmer".into(),
            ));
        }
        assert_safe_target(source)?;
        self.mounter.mount(source)
    }

    pub fn unmount(&self, target: &str, confirmed: bool) -> DiskResult<()> {
        if !confirmed {
            return Err(DiskError::Refused(
                "démontage refusé : passe --yes pour confirmer".into(),
            ));
        }
        assert_safe_target(target)?;
        self.mounter.unmount(target)
    }

    /// JSON plat pour la GUI (disques + enfants)
    pub fn list_json(&self) -> DiskResult<String> {
        let devices = self.list()?;
        #[derive(serde::Serialize)]
        struct Row<'a> {
            name: &'a str,
            path: &'a str,
            size: &'a str,
            fstype: Option<&'a str>,
            mountpoint: Option<&'a str>,
            label: Option<&'a str>,
            kind: &'a str,
            depth: usize,
        }
        fn walk<'a>(devs: &'a [BlockDevice], depth: usize, out: &mut Vec<Row<'a>>) {
            for d in devs {
                out.push(Row {
                    name: &d.name,
                    path: &d.path,
                    size: &d.size,
                    fstype: d.fstype.as_deref(),
                    mountpoint: d.mountpoint.as_deref(),
                    label: d.label.as_deref(),
                    kind: d.kind.as_str(),
                    depth,
                });
                walk(&d.children, depth + 1, out);
            }
        }
        let mut rows = Vec::new();
        walk(&devices, 0, &mut rows);
        serde_json::to_string_pretty(&rows)
            .map_err(|e| DiskError::Io(format!("json: {e}")))
    }

    pub fn gen_nix_text(&self, include_system: bool) -> DiskResult<String> {
        let devices = self.list()?;
        Ok(generate_nix_filesystems(&devices, include_system))
    }

    /// Écrit le snippet Nix. Confirmation obligatoire (confirmed).
    pub fn write_nix(&self, path: &Path, include_system: bool, confirmed: bool) -> DiskResult<()> {
        if !confirmed {
            return Err(DiskError::Refused(
                "écriture Nix refusée : passe --yes pour confirmer".into(),
            ));
        }
        let text = self.gen_nix_text(include_system)?;
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).map_err(|e| DiskError::Io(e.to_string()))?;
        }
        fs::write(path, text).map_err(|e| DiskError::Io(format!("écriture {path:?}: {e}")))?;
        Ok(())
    }

    pub fn default_nix_out_path() -> std::path::PathBuf {
        if let Ok(flake) = std::env::var("FRAY_FLAKE") {
            return Path::new(&flake).join("customConfig/hardware/generated-disks.nix");
        }
        let home = std::env::var("HOME").unwrap_or_else(|_| "/tmp".into());
        Path::new(&home).join(".config/fray/generated-disks.nix")
    }

    pub fn explain(&self) -> String {
        r#"fray-disk - viewer disques (hexagonal, lecture d'abord)
=======================================================
list                 lsblk (disques / partitions / FS / montage)
list-json            même liste en JSON (GUI)
info <name>          détail d'un nœud (ex. sda1, /dev/nvme0n1p2)
open                 lance GNOME Disks ou KDE Partition Manager
mount <dev> --yes    udisksctl mount (confirmation obligatoire)
umount <cible> --yes udisksctl unmount
gen-nix [--system]   affiche fileSystems Nix (ext4/btrfs/…)
write-nix [path] --yes  écrit le fichier (défaut: $FRAY_FLAKE/.../generated-disks.nix)

Pas de wipe / format / resize ici - utilise l'outil DE via « open ».
"#
        .into()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::domain::{BlockDevice, BlockKind};
    use std::cell::RefCell;

    struct MemLister(Vec<BlockDevice>);
    impl BlockLister for MemLister {
        fn list(&self) -> DiskResult<Vec<BlockDevice>> {
            Ok(self.0.clone())
        }
    }

    struct MemMounter {
        mounted: RefCell<Vec<String>>,
    }
    impl Mounter for MemMounter {
        fn mount(&self, source: &str) -> DiskResult<()> {
            self.mounted.borrow_mut().push(source.into());
            Ok(())
        }
        fn unmount(&self, target: &str) -> DiskResult<()> {
            self.mounted.borrow_mut().push(format!("umount:{target}"));
            Ok(())
        }
    }

    struct MemDesktop;
    impl DesktopDiskTool for MemDesktop {
        fn open(&self) -> DiskResult<()> {
            Ok(())
        }
    }

    fn sample() -> Vec<BlockDevice> {
        vec![BlockDevice {
            name: "vda".into(),
            path: "/dev/vda".into(),
            size: "20G".into(),
            fstype: None,
            mountpoint: None,
            label: None,
            kind: BlockKind::Disk,
            children: vec![BlockDevice {
                name: "vda1".into(),
                path: "/dev/vda1".into(),
                size: "20G".into(),
                fstype: Some("ext4".into()),
                mountpoint: Some("/".into()),
                label: None,
                kind: BlockKind::Part,
                children: vec![],
            }],
        }]
    }

    #[test]
    fn mount_requires_yes() {
        let l = MemLister(sample());
        let m = MemMounter {
            mounted: RefCell::new(vec![]),
        };
        let d = MemDesktop;
        let svc = DiskService {
            lister: &l,
            mounter: &m,
            desktop: &d,
        };
        assert!(svc.mount("/dev/sdb1", false).is_err());
        assert!(svc.mount("/dev/sdb1", true).is_ok());
        assert_eq!(m.mounted.borrow().as_slice(), ["/dev/sdb1"]);
    }

    #[test]
    fn list_text_contains_names() {
        let l = MemLister(sample());
        let m = MemMounter {
            mounted: RefCell::new(vec![]),
        };
        let d = MemDesktop;
        let svc = DiskService {
            lister: &l,
            mounter: &m,
            desktop: &d,
        };
        let t = svc.list_text().unwrap();
        assert!(t.contains("vda"));
        assert!(t.contains("vda1"));
    }
}
