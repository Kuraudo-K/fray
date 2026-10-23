# Desktop file
desktop_conf = configuration_data()
desktop_conf.set('bindir', get_option('prefix') / get_option('bindir'))

desktop_file = configure_file(
  input: 'org.fray.firewall.desktop.in',
  output: 'org.fray.firewall.desktop',
  configuration: desktop_conf,
  install: true,
  install_dir: get_option('datadir') / 'applications',
)

# Polkit policy
polkit_conf = configuration_data()
polkit_conf.set('bindir', get_option('prefix') / get_option('bindir'))

configure_file(
  input: 'org.fray.firewall.in',
  output: 'org.fray.firewall.policy',
  configuration: polkit_conf,
  install: true,
  install_dir: get_option('datadir') / 'polkit-1' / 'actions',
)

# Icons
subdir('icons')
