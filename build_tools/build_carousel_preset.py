"""Stage the custom carousel, its external images and the unified local package."""
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]


def main():
    version = json.loads((ROOT/'build_data/build_config.json').read_text())['game_version']
    output = ROOT/'build/unified/Driftkings-Carousel.zip'
    package = output.with_name('Driftkings.wotmod')
    if not package.is_file():
        raise ValueError('Build Driftkings.wotmod before packaging the carousel')
    config = ROOT/'res/configs/Driftkings/default/carousel_stats'
    icons = ROOT/'res/mods/Driftkings/Carroucel'
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        archive.write(package, 'mods/%s/Driftkings.wotmod' % version)
        for name in ('carousel.json', 'carouselNormal.json', 'carouselSmall.json'):
            json.loads((config/name).read_text(encoding='utf-8'))
            archive.write(config/name, 'mods/configs/Driftkings/default/carousel_stats/'+name)
        for path in sorted(icons.glob('*.png')):
            archive.write(path, 'mods/Driftkings/Carroucel/'+path.name)
        archive.write(ROOT/'docs/CAROUSEL_CUSTOM.md', 'CAROUSEL_CUSTOM.md')
        archive.write(ROOT/'docs/XVM-CONFIG-LICENSE.txt', 'XVM-CONFIG-LICENSE.txt')
        archive.write(ROOT/'source/scripts/client/Driftkings/core/carousel_tiers.py', 'source/carousel_tiers.py')
    print(output)


if __name__ == '__main__':
    main()
