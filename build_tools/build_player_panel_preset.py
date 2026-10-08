"""Package the panel/loading/TAB defaults without replacing rating preferences."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]


def main():
    folder = ROOT / 'res/configs/Driftkings/default/player_panel_pro'
    output = ROOT / 'build/unified/PlayerPanelPro-XVM-preset.zip'
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        for path in sorted(folder.glob('*.json')):
            if path.name != 'general.json':
                archive.write(path, path.name)
        for name in ('XVM-CONFIG-NOTICE.md', 'XVM-CONFIG-LICENSE.txt', 'PLAYER_PANEL_PRO.md'):
            archive.write(ROOT / 'docs' / name, name)
    print(output)
    # Targeted visual preset: leave loading, TAB, mode profiles and rating choices alone.
    output = output.with_name('PlayerPanelPro-HP-Spotted-preset.zip')
    if output.is_file():
        with ZipFile(output) as archive:
            if archive.namelist()==['playersPanel.json'] and archive.read('playersPanel.json')==(folder / 'playersPanel.json').read_bytes():
                print(str(output)+' (unchanged)')
                return
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        archive.write(folder / 'playersPanel.json', 'playersPanel.json')
    print(output)


if __name__ == '__main__':
    main()
