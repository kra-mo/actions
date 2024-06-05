moduledir = python_dir / 'actions'

blueprints = custom_target('blueprints',
  input: files(
    'gtk/help-overlay.blp',
    'gtk/window.blp',
  ),
  output: '.',
  command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@'],
)

gnome.compile_resources('actions',
  configure_file(
    input: 'actions.gresource.xml.in',
    output: 'actions.gresource.xml',
    configuration: conf
  ),
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
  dependencies: blueprints,
)

python = import('python')

configure_file(
  input: 'actions.in',
  output: 'actions',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x'
)

actions_sources = [
  '__init__.py',
  'actions.py',
  'main.py',
  'variables.py',
  'window.py',
  configure_file(
    input: 'shared.py.in',
    output: 'shared.py',
    configuration: conf
  )
]

install_data(actions_sources, install_dir: moduledir)
