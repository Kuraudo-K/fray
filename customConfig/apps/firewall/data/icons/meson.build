install_data(
  'fray-firewall.svg',
  install_dir: get_option('datadir') / 'icons' / 'hicolor' / 'scalable' / 'apps',
  rename: 'org.fray.firewall.svg',
)

foreach size : ['16', '32', '48', '64', '128', '256', '512']
  install_data(
    'fray-firewall-' + size + 'x' + size + '.png',
    install_dir: get_option('datadir') / 'icons' / 'hicolor' / (size + 'x' + size) / 'apps',
    rename: 'org.fray.firewall.png',
  )
endforeach
