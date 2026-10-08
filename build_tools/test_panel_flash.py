"""Run the actual panel renderer against synthetic native holders in AIR.

Uses local SDKs, writes only build/flash-tests, and never launches the game.
AIR verifies AS3 behavior; Scaleform performance still requires a replay.
"""
import argparse
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PROGRAMS = ROOT.parent.parent / 'Programas'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--air-sdk', type=Path, default=PROGRAMS / 'SDK/AIRSDK_51.2.1')
    parser.add_argument('--flex-sdk', type=Path, default=PROGRAMS / 'Flex')
    parser.add_argument('--suite', choices=('panel', 'hud', 'minimap', 'utils'), default='panel')
    args = parser.parse_args()
    test_class = {'panel': 'PanelRenderTest', 'hud': 'HudVisibilityTest', 'minimap': 'MinimapAimTest',
                  'utils': 'SharedUtilsTest'}[args.suite]
    output = ROOT / ('build/flash-tests' + ('-' + args.suite if args.suite != 'panel' else ''))
    output.mkdir(parents=True, exist_ok=True)
    sources = ROOT / 'flash_source/battle/src'
    tests = ROOT / 'build_tools/tests/flash'
    command = ['java', '-jar', str(args.flex_sdk / 'lib/mxmlc.jar'),
               '+flexlib=' + str(args.flex_sdk / 'frameworks'), '-load-config=',
               '-compiler.theme=', '-compiler.library-path=',
               '-compiler.external-library-path=' + str(args.air_sdk / 'frameworks/libs/air/airglobal.swc'),
               '-compiler.source-path=' + str(tests) + ',' + str(sources) + ',' + str(ROOT / 'flash_source/shared/as3'),
               '-target-player=11.1', '-swf-version=14', '-debug=true',
               '-output=' + str(output / (test_class + '.swf')), str(tests / (test_class + '.as'))]
    subprocess.run(command, cwd=ROOT, check=True, timeout=90)
    app = ET.Element('application', xmlns='http://ns.adobe.com/air/application/51.1')
    for key, value in [('id', 'driftkings.tests.' + args.suite), ('filename', test_class), ('versionNumber', '1.0')]:
        ET.SubElement(app, key).text = value
    window = ET.SubElement(app, 'initialWindow')
    ET.SubElement(window, 'content').text = test_class + '.swf'
    ET.SubElement(window, 'visible').text = 'false'
    descriptor = output / 'application.xml'
    ET.ElementTree(app).write(descriptor, encoding='utf-8', xml_declaration=True)
    report = output / 'result.txt'
    report.unlink(missing_ok=True)
    result = subprocess.run([str(args.air_sdk / 'bin/adl.exe'), str(descriptor)],
                            cwd=output, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=45,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    details = result.stdout + (report.read_text(encoding='utf-8') if report.exists() else '')
    print(details)
    (output / 'test.log').write_text(details, encoding='utf-8')
    if result.returncode or 'PASS ' + test_class not in details:
        raise SystemExit(result.returncode or 1)


if __name__ == '__main__':
    main()
