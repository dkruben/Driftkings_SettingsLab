"""Build the pinned native marker movie with the integrated Flash fields."""
import hashlib
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path
from build_tools.vehicle_markers_patch import patch_marker, patch_manager, inject_helper, swf_parts


def build(root, destination, spec, tools, game_root):
    lock = json.loads((root / spec['lock']).read_text(encoding='utf-8'))
    with zipfile.ZipFile(Path(game_root) / 'res/packages' / lock['package']) as archive:
        native = archive.read(lock['resource'])
    if hashlib.sha256(native).hexdigest() != lock['sha256']:
        raise ValueError('Vehicle marker native movie changed; review the pinned patch before building')
    binary = Path(tools['rabcdasm_home'])
    sdk = Path(tools['flex_home'])
    with tempfile.TemporaryDirectory(prefix='vehicle-markers-', dir=str(destination.parent)) as directory:
        work = Path(directory)
        def run(command):
            subprocess.check_call([str(x) for x in command], cwd=str(work))
        helper = work / 'fields.swf'
        run([tools['java'], '-Xmx512m', '-jar', tools['mxmlc_jar'], '+flexlib=' + str(sdk / 'frameworks'),
             '-load-config=', '-compiler.theme=', '-compiler.external-library-path=' + tools['playerglobal'],
             '-target-player=11.0', '-swf-version=13', '-debug=false', '-compiler.strict=true',
             '-compiler.source-path+=' + str(root / 'flash_source/shared/as3'),
             '-compiler.library-path=' + str(sdk / 'frameworks/libs/framework.swc'),
             '-compiler.optimize=true', '-output=' + str(helper), root / spec['entrypoint']])
        movie = work / 'markers.swf'
        movie.write_bytes(native)
        run([binary / 'abcexport.exe', movie])
        run([binary / 'rabcdasm.exe', work / 'markers-0.abc'])
        disassembly = work / 'markers-0'
        base = disassembly / 'net/wg/gui/battle/views/vehicleMarkers'
        for filename, patch in (('VehicleMarker.class.asasm', patch_marker), ('VehicleMarkersManager.class.asasm', patch_manager)):
            path = base / filename
            path.write_text(patch(path.read_text()), encoding='utf-8')
        run([binary / 'rabcasm.exe', disassembly / 'markers-0.main.asasm'])
        run([binary / 'abcreplace.exe', movie, '0', disassembly / 'markers-0.main.abc'])
        output = inject_helper(movie.read_bytes(), helper.read_bytes())
        _, tags = swf_parts(output)
        if sum(kind == 82 for kind, tag in tags) != 2:
            raise ValueError('Unexpected marker ABC count')
        destination.write_bytes(output)
