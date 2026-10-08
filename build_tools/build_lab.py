"""Compile the isolated laboratory and produce one wotmod; no deployment."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--flash', action='store_true', help='Recompile and publish local Flash assets first')
    parser.add_argument('--hg', default=str(Path(os.environ.get('LOCALAPPDATA', '')) /
                        'Atlassian/SourceTree/hg_local/hg.exe'), help='Mercurial executable embedding Python 2.7')
    args = parser.parse_args()
    if not Path(args.hg).is_file():
        parser.error('Python 2.7 host not found; specify --hg')
    subprocess.check_call([sys.executable, 'build_tools/check_flash_contracts.py'], cwd=str(ROOT))
    subprocess.check_call([args.hg, '--config',
                           'extensions.dksmoke=build_tools/python27_hooks_smoke.py', 'dksmoke'], cwd=str(ROOT))
    subprocess.check_call([sys.executable, 'build_tools/build_unified.py', '--prepare'], cwd=str(ROOT))
    subprocess.check_call([sys.executable, 'build_tools/build_ui_resources.py'], cwd=str(ROOT))
    carousel_manifest = ROOT / 'build_data/components/CarouselStats.json'
    if json.loads(carousel_manifest.read_text()).get('enabled'):
        subprocess.check_call([sys.executable, 'build_tools/build_carousel_bridge.py'], cwd=str(ROOT))
    if args.flash:
        subprocess.check_call([sys.executable, 'build_tools/build_flash.py', '--publish'], cwd=str(ROOT))
    (ROOT / 'build').mkdir(exist_ok=True)
    with (ROOT / 'build/lab-compile.log').open('wb') as log:
        subprocess.check_call([args.hg, '--config',
                               'extensions.dkbuild=build_tools/python27_lab_runner.py', 'dkbuild'],
                              cwd=str(ROOT), stdout=log, stderr=subprocess.STDOUT)
    subprocess.check_call([sys.executable, 'build_tools/build_unified.py'], cwd=str(ROOT))
    subprocess.check_call([sys.executable, 'build_tools/build_player_panel_preset.py'], cwd=str(ROOT))
    subprocess.check_call([sys.executable, 'build_tools/build_carousel_preset.py'], cwd=str(ROOT))


if __name__ == '__main__':
    main()
