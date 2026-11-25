"""Build the pinned native marker movie with the integrated Flash fields."""
from contextlib import contextmanager
import hashlib
import json
import os
import subprocess
import tempfile
import zipfile
from pathlib import Path
from build_tools.isolated_output import active_output, tool_environment
from build_tools.validate_build_data import source_client
from build_tools.vehicle_markers_patch import (inject_helper, marker_lock_for_build, patch_manager, patch_marker,
                                              swf_parts, verify_manager_contract, verify_marker_contract,
                                              verify_native_movie)


# Budget for the complete relative disassembly tree, not specific observed names.
# The pinned movie currently needs 107 chars; allow 120 and reserve 8 more.
DISASSEMBLY_BUDGET = 120
PATH_MARGIN = 8
SHORT_WORKSPACE_FOLDER = 'DK_TMP'


def too_deep(path):
    return len(str(path).encode('utf-16-le')) // 2 + 1 + DISASSEMBLY_BUDGET + PATH_MARGIN >= 260


def short_workspace_root(root):
    """Short location for the marker disassembly when the run folder is too deep.

    DK_MARKER_WORKSPACE overrides it; the default is a folder on the drive of the repository.
    """
    configured = os.environ.get('DK_MARKER_WORKSPACE')
    return Path(configured) if configured else Path(Path(root).absolute().anchor) / SHORT_WORKSPACE_FOLDER


@contextmanager
def short_marker_workspace(scope, short_root, protected=()):
    """Run-owned workspace outside the isolated run folder; same path budget, never shared."""
    work = Path(short_root) / ('vm_' + scope.run_id)
    if too_deep(work):
        raise ValueError('Short marker workspace too deep for safe Windows paths')
    work = scope.adopt(work, protected)
    try:
        # Diagnostics stay with the run: record where the disassembly happened.
        (scope.check(scope.path / 'workspace' / 'marker_workspace.txt')).write_text(str(work), encoding='utf-8')
        print('Marker workspace: ' + str(work), flush=True)
        yield work
    except BaseException as original:
        try:
            scope.release(work)
        except BaseException as cleanup_error:
            raise cleanup_error from original
        raise
    else:
        scope.release(work)


@contextmanager
def marker_workspace(destination, short_root=None, protected=()):
    scope = active_output()
    if scope is None:
        with tempfile.TemporaryDirectory(prefix='vehicle-markers-', dir=str(destination.parent)) as directory:
            yield Path(directory)
        return
    scope.check(destination)
    parent = scope.check(scope.path / 'workspace/tmp')
    # tempfile's random suffix is eight characters on the supported runtime.
    projected = parent / ('vm-' + 'x' * 8)
    if too_deep(projected):
        if short_root is None:
            raise ValueError('Isolated marker workspace too deep for safe Windows paths')
        with short_marker_workspace(scope, short_root, protected) as work:
            yield work
        return
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



def build(root, destination, spec, tools, game_root, library_manifest='flash_source/shared/swc/manifest.json'):
    config = json.loads((root / 'build_data/build_config.json').read_text(encoding='utf-8'))
    build_id = source_client(game_root, config)['build']
    locks = {key: json.loads((root / value).read_text(encoding='utf-8')) for key, value in spec['locks'].items()}
    lock = marker_lock_for_build(locks, build_id)
    with zipfile.ZipFile(Path(game_root) / 'res/packages' / lock['package']) as archive:
        native = verify_native_movie(archive.read(lock['resource']), lock)
    binary = Path(tools['rabcdasm_home'])
    sdk = Path(tools['flex_home'])
    libraries = root / library_manifest
    external_libraries = []
    for item in json.loads(libraries.read_text(encoding='utf-8'))['libraries']:
        library = libraries.parent / item['name']
        if hashlib.sha256(library.read_bytes()).hexdigest().lower() != item['sha256'].lower():
            raise ValueError('Flash library hash mismatch: ' + item['name'])
        external_libraries.append('-compiler.external-library-path+=' + str(library))
    with marker_workspace(destination, short_workspace_root(root),
                          (game_root, tools.get('reference_root'), tools.get('rabcdasm_home'))) as work:
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
        for filename, verify, patch in (('VehicleMarker.class.asasm', verify_marker_contract, patch_marker),
                                        ('VehicleMarkersManager.class.asasm', verify_manager_contract, patch_manager)):
            path = base / filename
            text = path.read_text()
            verify(text)
            path.write_text(patch(text), encoding='utf-8')
        run([binary / 'rabcasm.exe', disassembly / 'markers-0.main.asasm'])
        run([binary / 'abcreplace.exe', movie, '0', disassembly / 'markers-0.main.abc'])
        output = inject_helper(movie.read_bytes(), helper.read_bytes())
        _, tags = swf_parts(output)
        if sum(kind == 82 for kind, tag in tags) != 2:
            raise ValueError('Unexpected marker ABC count')
        destination.write_bytes(output)
