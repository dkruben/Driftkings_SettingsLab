"""Build the pinned native marker movie with the integrated Flash fields."""
from contextlib import contextmanager
import hashlib
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path
from build_tools.isolated_output import active_output, tool_environment
from build_tools.vehicle_markers_patch import patch_marker, patch_manager, inject_helper, swf_parts


# Budget for the complete relative disassembly tree, not specific observed names.
# The pinned movie currently needs 107 chars; allow 120 and reserve 8 more.
DISASSEMBLY_BUDGET = 120
PATH_MARGIN = 8


@contextmanager
def marker_workspace(destination):
    scope = active_output()
    if scope is None:
        with tempfile.TemporaryDirectory(prefix='vehicle-markers-', dir=str(destination.parent)) as directory:
            yield Path(directory)
        return
    scope.check(destination)
    parent = scope.check(scope.path / 'workspace/tmp')
    # tempfile's random suffix is eight characters on the supported runtime.
    projected = parent / ('vm-' + 'x' * 8)
    if len(str(projected).encode('utf-16-le')) // 2 + 1 + DISASSEMBLY_BUDGET + PATH_MARGIN >= 260:
        raise ValueError('Isolated marker workspace too deep for safe Windows paths')
    parent.mkdir(exist_ok=True)
    temporary = tempfile.TemporaryDirectory(prefix='vm-', dir=str(parent))
    work = Path(temporary.name)
    try:
        scope.check(work)
        if len(str(work).encode('utf-16-le')) // 2 + 1 + DISASSEMBLY_BUDGET + PATH_MARGIN >= 260:
            raise ValueError('Actual marker temporary path exceeds Windows budget')
        yield work
    except BaseException as original:
        try:
            scope.unpin_tree(work)
            temporary.cleanup()
        except BaseException as cleanup_error:
            # Preserve both failures; cleanup remains blocking.
            raise cleanup_error from original
        raise
    else:
        scope.unpin_tree(work)
        temporary.cleanup()



def build(root, destination, spec, tools, game_root):
    lock = json.loads((root / spec['lock']).read_text(encoding='utf-8'))
    with zipfile.ZipFile(Path(game_root) / 'res/packages' / lock['package']) as archive:
        native = archive.read(lock['resource'])
    if hashlib.sha256(native).hexdigest() != lock['sha256']:
        raise ValueError('Vehicle marker native movie changed; review the pinned patch before building')
    binary = Path(tools['rabcdasm_home'])
    sdk = Path(tools['flex_home'])
    libraries = root / 'flash_source/shared/swc/manifest.json'
    external_libraries = []
    for item in json.loads(libraries.read_text(encoding='utf-8'))['libraries']:
        library = libraries.parent / item['name']
        if hashlib.sha256(library.read_bytes()).hexdigest().lower() != item['sha256'].lower():
            raise ValueError('Flash library hash mismatch: ' + item['name'])
        external_libraries.append('-compiler.external-library-path+=' + str(library))
    with marker_workspace(destination) as work:
        def run(command):
            scope = active_output()
            if scope:
                scope.check(work)
            subprocess.check_call([str(x) for x in command], cwd=str(work), env=tool_environment())
        helper = work / 'fields.swf'
        run([tools['java'], '-Xmx512m', '-jar', tools['mxmlc_jar'], '+flexlib=' + str(sdk / 'frameworks'),
             '-load-config=', '-compiler.theme=', '-compiler.external-library-path=' + tools['playerglobal'],
             *external_libraries,
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
        for filename, patch in (('VehicleMarker.class.asasm', patch_marker),
                                ('VehicleMarkersManager.class.asasm', patch_manager)):
            path = base / filename
            path.write_text(patch(path.read_text()), encoding='utf-8')
        run([binary / 'rabcasm.exe', disassembly / 'markers-0.main.asasm'])
        run([binary / 'abcreplace.exe', movie, '0', disassembly / 'markers-0.main.abc'])
        output = inject_helper(movie.read_bytes(), helper.read_bytes())
        _, tags = swf_parts(output)
        if sum(kind == 82 for kind, tag in tags) != 2:
            raise ValueError('Unexpected marker ABC count')
        destination.write_bytes(output)
