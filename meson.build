project(
    'Better Control',
    'c',
    default_options: ['c_std=gnu23', 'warning_level=3'],
    version: '0.0.1',
    license: 'GPL-3.0-or-later',
    license_files: ['COPYING'],
)

deps = [dependency('gtk+-3.0')]
args = [
    '-DAPP_VERSION="' + meson.project_version() + '"',
    '-DAPP_NAME="' + meson.project_name() + '"',
    '-DAPP_ID="org.BetterDE.Better-Control"',
    '-DAPP_PREFIX="/org/BetterDE/Better-Control"',
]

if get_option('network-tab')
    deps += dependency('libnm')
    args += '-DNETWORK_TAB'
endif

if get_option('volume-tab')
    deps += dependency('libpipewire-0.3')
    args += '-DVOLUME_TAB'
endif

gnome = import('gnome')

data = gnome.compile_resources(
    'resources',
    'assets/bc.gresource.xml',
    source_dir: 'assets',
    c_name: 'resources',
)

subdir('src')
executable(
    'better-control',
    [source_files, data],
    include_directories: include_directories('include'),
    dependencies: deps,
    c_args: args,
    install: true,
)