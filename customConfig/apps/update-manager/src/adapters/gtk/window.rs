use std::cell::Cell;
use std::rc::Rc;
use std::sync::Arc;

use gtk::prelude::*;

use crate::adapters::config::AppConfig;
use crate::adapters::gtk::theme_apply;
use crate::application::UpdateManagerService;
use crate::domain::{PowerMode, Settings, Weekday, POWER_MODE_LABELS, WEEKDAY_LABELS};
use crate::ports::IconLocator;

pub fn run(service: Arc<UpdateManagerService>, config: AppConfig, icons: Arc<dyn IconLocator>) {
    glib::set_prgname(Some("fray-update-manager"));
    if let Err(err) = gtk::init() {
        eprintln!("Impossible d'initialiser GTK : {err}");
        eprintln!("Sur NixOS : nix-shell -p pkg-config gtk3 --run 'cargo run --release'");
        std::process::exit(1);
    }
    let _ = gdk::set_program_class("fray-update-manager");
    theme_apply::apply_gtk_theme();
    let _gnome = theme_apply::watch_gnome_theme();

    let app = App::new(service, config, icons);
    app.wire();
    app.window.show_all();
    gtk::main();
}

struct App {
    window: gtk::Window,
    service: Arc<UpdateManagerService>,
    sw_auto: gtk::Switch,
    sw_sched: gtk::Switch,
    fr_sched: gtk::Frame,
    combo_day: gtk::ComboBoxText,
    spin_h: gtk::SpinButton,
    spin_m: gtk::SpinButton,
    pow_buttons: Vec<(PowerMode, gtk::RadioButton)>,
    status: gtk::Label,
    sys_status: gtk::Label,
    btn_apply: gtk::Button,
    btn_update: gtk::Button,
    busy: Cell<bool>,
    last_dark: Cell<bool>,
    _poll: Cell<Option<glib::SourceId>>,
}

impl App {
    fn new(
        service: Arc<UpdateManagerService>,
        config: AppConfig,
        icons: Arc<dyn IconLocator>,
    ) -> Rc<Self> {
        let cfg = service.load_settings();
        let window = gtk::Window::new(gtk::WindowType::Toplevel);
        window.set_title("Mises à jour Fray");
        window.set_default_size(440, 560);
        window.set_border_width(16);
        if let Some(icon) = icons.resolve_png() {
            let _ = window.set_icon_from_file(&icon);
            let _ = gtk::Window::set_default_icon_from_file(&icon);
        }

        let root = gtk::Box::new(gtk::Orientation::Vertical, 14);
        window.add(&root);

        let title = gtk::Label::new(None);
        title.set_markup("<span size='large'><b>Mises à jour Fray</b></span>");
        root.pack_start(&title, false, false, 0);

        if config.demo {
            let demo = gtk::Label::new(Some("MODE DÉMO — rien n'est écrit sur le système réel"));
            demo.set_line_wrap(true);
            root.pack_start(&demo, false, false, 0);
        }

        let fr_auto = gtk::Frame::new(Some("Mise à jour automatique"));
        let box_auto = gtk::Box::new(gtk::Orientation::Vertical, 8);
        box_auto.set_border_width(10);
        fr_auto.add(&box_auto);
        root.pack_start(&fr_auto, false, false, 0);

        let sw_auto = gtk::Switch::new();
        sw_auto.set_active(cfg.auto_upgrade);
        let row = gtk::Box::new(gtk::Orientation::Horizontal, 10);
        let lbl = gtk::Label::new(Some("Auto au lancement (boot + toutes les 12 h)"));
        lbl.set_xalign(0.0);
        lbl.set_line_wrap(true);
        row.pack_start(&lbl, true, true, 0);
        row.pack_end(&sw_auto, false, false, 0);
        box_auto.pack_start(&row, false, false, 0);

        let hint = gtk::Label::new(None);
        hint.set_markup(
            "<span size='small'>Désactivez l'auto pour utiliser la planification.</span>",
        );
        hint.set_xalign(0.0);
        hint.set_line_wrap(true);
        box_auto.pack_start(&hint, false, false, 0);

        let sys_status = gtk::Label::new(Some(""));
        sys_status.set_xalign(0.0);
        sys_status.set_line_wrap(true);
        sys_status.set_selectable(true);
        box_auto.pack_start(&sys_status, false, false, 0);

        let fr_sched = gtk::Frame::new(Some("Planification (si auto désactivée)"));
        let box_sched = gtk::Box::new(gtk::Orientation::Vertical, 8);
        box_sched.set_border_width(10);
        fr_sched.add(&box_sched);
        root.pack_start(&fr_sched, false, false, 0);

        let sw_sched = gtk::Switch::new();
        sw_sched.set_active(cfg.schedule_enable);
        let row2 = gtk::Box::new(gtk::Orientation::Horizontal, 10);
        let lbl2 = gtk::Label::new(Some("Mise à jour planifiée chaque semaine"));
        lbl2.set_xalign(0.0);
        row2.pack_start(&lbl2, true, true, 0);
        row2.pack_end(&sw_sched, false, false, 0);
        box_sched.pack_start(&row2, false, false, 0);

        let grid = gtk::Grid::new();
        grid.set_column_spacing(10);
        grid.set_row_spacing(8);
        box_sched.pack_start(&grid, false, false, 0);

        let day_label = gtk::Label::new(Some("Jour"));
        day_label.set_xalign(0.0);
        grid.attach(&day_label, 0, 0, 1, 1);
        let combo_day = gtk::ComboBoxText::new();
        for (day, label) in WEEKDAY_LABELS {
            combo_day.append(Some(day.as_str()), label);
        }
        combo_day.set_active_id(Some(cfg.weekday.as_str()));
        grid.attach(&combo_day, 1, 0, 1, 1);

        let hour_label = gtk::Label::new(Some("Heure"));
        hour_label.set_xalign(0.0);
        grid.attach(&hour_label, 0, 1, 1, 1);
        let time_box = gtk::Box::new(gtk::Orientation::Horizontal, 4);
        let spin_h = gtk::SpinButton::with_range(0.0, 23.0, 1.0);
        spin_h.set_digits(0);
        spin_h.set_value(f64::from(cfg.hour));
        let spin_m = gtk::SpinButton::with_range(0.0, 59.0, 1.0);
        spin_m.set_digits(0);
        spin_m.set_value(f64::from(cfg.minute));
        time_box.pack_start(&spin_h, false, false, 0);
        time_box.pack_start(&gtk::Label::new(Some(":")), false, false, 0);
        time_box.pack_start(&spin_m, false, false, 0);
        grid.attach(&time_box, 1, 1, 1, 1);

        let fr_pow = gtk::Frame::new(Some("Puissance pendant la mise à jour"));
        let box_pow = gtk::Box::new(gtk::Orientation::Vertical, 6);
        box_pow.set_border_width(10);
        fr_pow.add(&box_pow);
        root.pack_start(&fr_pow, false, false, 0);

        let mut pow_buttons = Vec::new();
        let mut group: Option<gtk::RadioButton> = None;
        for (mode, label) in POWER_MODE_LABELS {
            let rb = match &group {
                None => gtk::RadioButton::with_label(label),
                Some(leader) => gtk::RadioButton::with_label_from_widget(leader, label),
            };
            if group.is_none() {
                group = Some(rb.clone());
            }
            rb.set_active(cfg.power_mode == *mode);
            pow_buttons.push((*mode, rb.clone()));
            box_pow.pack_start(&rb, false, false, 0);
        }

        let status = gtk::Label::new(Some(""));
        status.set_xalign(0.0);
        status.set_line_wrap(true);
        status.set_max_width_chars(56);
        root.pack_start(&status, false, false, 0);

        let btn_row = gtk::Box::new(gtk::Orientation::Horizontal, 8);
        root.pack_start(&btn_row, false, false, 0);
        let btn_apply = gtk::Button::with_label("Appliquer la config");
        let btn_update = gtk::Button::with_label("Mettre à jour maintenant");
        btn_update.style_context().add_class("suggested-action");
        btn_row.pack_start(&btn_apply, true, true, 0);
        btn_row.pack_start(&btn_update, true, true, 0);

        let app = Rc::new(Self {
            window,
            service,
            sw_auto,
            sw_sched,
            fr_sched,
            combo_day,
            spin_h,
            spin_m,
            pow_buttons,
            status,
            sys_status,
            btn_apply,
            btn_update,
            busy: Cell::new(false),
            last_dark: Cell::new(false),
            _poll: Cell::new(None),
        });
        app.last_dark.set(app.service.prefers_dark());
        app.refresh_sys_status();
        app
    }

    fn wire(self: &Rc<Self>) {
        for (mode, button) in &self.pow_buttons {
            let app = self.clone();
            let mode = *mode;
            button.connect_toggled(move |button| {
                if !button.is_active() {
                    return;
                }
                match app.service.set_power_mode(mode) {
                    Ok(()) => app.set_status(
                        &format!("Mode puissance : {} (immédiat).", mode.as_str()),
                        false,
                    ),
                    Err(err) => {
                        app.set_status(&format!("Impossible d'écrire le mode : {err}"), true);
                    }
                }
            });
        }

        let app = self.clone();
        self.sw_auto
            .connect_notify_local(Some("active"), move |_, _| {
                app.sync_sensitivity();
            });
        let app = self.clone();
        self.sw_sched
            .connect_notify_local(Some("active"), move |_, _| {
                app.sync_sensitivity();
            });

        let app = self.clone();
        self.btn_apply.connect_clicked(move |_| app.on_apply());
        let app = self.clone();
        self.btn_update.connect_clicked(move |_| app.on_update());

        let app = self.clone();
        self.window.connect_destroy(move |_| {
            if let Some(source) = app._poll.take() {
                source.remove();
            }
            gtk::main_quit();
        });

        self.sync_sensitivity();

        let app = self.clone();
        let poll = glib::timeout_add_seconds_local(2, move || {
            app.poll_theme();
            glib::ControlFlow::Continue
        });
        self._poll.set(Some(poll));
    }

    fn poll_theme(&self) {
        let dark = self.service.prefers_dark();
        if dark != self.last_dark.get() {
            self.last_dark.set(dark);
            theme_apply::apply_gtk_theme();
            self.window.queue_draw();
        }
    }

    fn refresh_sys_status(&self) {
        let text = self.service.system_status().display_lines().join("\n");
        self.sys_status.set_text(&text);
    }

    fn collect(&self) -> Settings {
        let auto = self.sw_auto.is_active();
        let sched = self.sw_sched.is_active() && !auto;
        let weekday = self
            .combo_day
            .active_id()
            .and_then(|id| Weekday::parse(id.as_str()))
            .unwrap_or(Weekday::Sat);
        let power_mode = self
            .pow_buttons
            .iter()
            .find(|(_, button)| button.is_active())
            .map(|(mode, _)| *mode)
            .unwrap_or(PowerMode::Standard);
        Settings::from_ui(
            auto,
            sched,
            weekday,
            self.spin_h.value().clamp(0.0, 23.0) as u8,
            self.spin_m.value().clamp(0.0, 59.0) as u8,
            power_mode,
        )
    }

    fn sync_sensitivity(&self) {
        let auto = self.sw_auto.is_active();
        self.fr_sched.set_sensitive(!auto);
        if auto && self.sw_sched.is_active() {
            self.sw_sched.set_active(false);
        }
        let sched_on = self.sw_sched.is_active() && !auto;
        self.combo_day.set_sensitive(sched_on);
        self.spin_h.set_sensitive(sched_on);
        self.spin_m.set_sensitive(sched_on);
    }

    fn set_busy(&self, busy: bool) {
        self.busy.set(busy);
        self.btn_apply.set_sensitive(!busy);
        self.btn_update.set_sensitive(!busy);
    }

    fn set_status(&self, text: &str, error: bool) {
        if error {
            let escaped = glib::markup_escape_text(text);
            self.status
                .set_markup(&format!("<span foreground='#c62828'>{escaped}</span>"));
        } else {
            self.status.set_text(text);
        }
    }

    fn on_apply(self: &Rc<Self>) {
        if self.busy.get() {
            return;
        }
        let cfg = self.collect();
        self.set_busy(true);
        self.set_status(
            "Écriture des préférences… puis nh os switch (mot de passe si demandé)…",
            false,
        );

        let service = self.service.clone();
        let app = self.clone();
        let (tx, rx) = std::sync::mpsc::channel();
        std::thread::spawn(move || {
            let _ = tx.send(service.apply_settings(&cfg));
        });
        glib::timeout_add_local(std::time::Duration::from_millis(50), move || {
            match rx.try_recv() {
                Ok(result) => {
                    app.finish_apply(result);
                    glib::ControlFlow::Break
                }
                Err(std::sync::mpsc::TryRecvError::Empty) => glib::ControlFlow::Continue,
                Err(std::sync::mpsc::TryRecvError::Disconnected) => {
                    app.set_busy(false);
                    app.set_status("Échec interne (canal coupé).", true);
                    glib::ControlFlow::Break
                }
            }
        });
    }

    fn finish_apply(&self, result: crate::ports::OpResult) {
        self.set_busy(false);
        self.refresh_sys_status();
        let (msg, error) = self.service.apply_status_message(&result);
        self.set_status(&msg, error);
        if !result.ok
            && !result.detail.is_empty()
            && (result.detail.chars().count() > 120 || result.detail.contains('\n'))
        {
            show_log_dialog(&self.window, "Détails — application config", &result.detail);
        }
    }

    fn on_update(self: &Rc<Self>) {
        if self.busy.get() {
            return;
        }
        let cfg = self.collect();
        self.set_busy(true);
        self.set_status("Lancement de fray-update…", false);

        let service = self.service.clone();
        let app = self.clone();
        let (tx, rx) = std::sync::mpsc::channel();
        std::thread::spawn(move || {
            let _ = tx.send(service.update_now(&cfg));
        });
        glib::timeout_add_local(std::time::Duration::from_millis(50), move || {
            match rx.try_recv() {
                Ok(result) => {
                    app.finish_update(result);
                    glib::ControlFlow::Break
                }
                Err(std::sync::mpsc::TryRecvError::Empty) => glib::ControlFlow::Continue,
                Err(std::sync::mpsc::TryRecvError::Disconnected) => {
                    app.set_busy(false);
                    app.set_status("Échec interne (canal coupé).", true);
                    glib::ControlFlow::Break
                }
            }
        });
    }

    fn finish_update(&self, result: crate::ports::OpResult) {
        self.set_busy(false);
        let (msg, error) = self.service.update_status_message(&result);
        self.set_status(&msg, error);
        if !result.detail.is_empty()
            && (result.detail.chars().count() > 80 || result.detail.contains('\n'))
        {
            let title = if result.ok {
                "Log — mise à jour"
            } else {
                "Détails — échec màj"
            };
            show_log_dialog(&self.window, title, &result.detail);
        }
    }
}

fn show_log_dialog(parent: &gtk::Window, title: &str, text: &str) {
    // Ré-appliquer le thème (KDE sombre) avant d'ouvrir la petite fenêtre.
    theme_apply::apply_gtk_theme();

    let dlg = gtk::Dialog::with_buttons(
        Some(title),
        Some(parent),
        gtk::DialogFlags::MODAL,
        &[("Fermer", gtk::ResponseType::Close)],
    );
    dlg.set_default_size(560, 420);
    dlg.set_resizable(true);
    let content = dlg.content_area();
    content.set_border_width(10);
    content.set_spacing(8);

    let hint = gtk::Label::new(Some("Défilez pour voir tout le log."));
    hint.set_xalign(0.0);
    content.pack_start(&hint, false, false, 0);

    let scrolled = gtk::ScrolledWindow::new(None::<&gtk::Adjustment>, None::<&gtk::Adjustment>);
    scrolled.set_policy(gtk::PolicyType::Automatic, gtk::PolicyType::Automatic);
    scrolled.set_shadow_type(gtk::ShadowType::In);
    scrolled.set_size_request(520, 320);
    scrolled.set_hexpand(true);
    scrolled.set_vexpand(true);

    let tv = gtk::TextView::new();
    tv.set_editable(false);
    tv.set_cursor_visible(false);
    tv.set_wrap_mode(gtk::WrapMode::WordChar);
    tv.set_monospace(true);
    let body = if text.is_empty() { "(vide)" } else { text };
    tv.buffer().expect("text buffer").set_text(body);
    scrolled.add(&tv);
    content.pack_start(&scrolled, true, true, 0);

    theme_apply::style_log_surfaces(&dlg, &tv);

    dlg.show_all();
    let _ = dlg.run();
    unsafe {
        dlg.destroy();
    }
}
