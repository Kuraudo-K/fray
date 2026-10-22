//! Cas d'usage

use crate::domain::{
    assert_safe_target, find_by_name, format_row, BlockDevice, DiskError, DiskResult,
};
use crate::ports::{BlockLister, DesktopDiskTool, Mounter};

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

    /// Montage via udisks — confirmation côté CLI (flag --yes)
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

    pub fn explain(&self) -> String {
        r#"fray-disk — viewer disques (hexagonal, lecture d'abord)
=======================================================
list              lsblk (disques / partitions / FS / montage)
info <name>       détail d'un nœud (ex. sda1, /dev/nvme0n1p2)
open              lance GNOME Disks ou KDE Partition Manager
mount <dev> --yes  udisksctl mount (confirmation obligatoire)
umount <cible> --yes  udisksctl unmount

Pas de wipe / format / resize ici — utilise l'outil DE via « open ».
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
