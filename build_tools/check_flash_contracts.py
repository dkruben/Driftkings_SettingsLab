"""Check owned Python meta contracts against the actual ActionScript sources."""
import ast
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def methods_for(name, classes):
    node = classes.get(name)
    if node is None:
        return {}
    methods = {}
    for base in node.bases:
        if isinstance(base, ast.Name):
            methods.update(methods_for(base.id, classes))
    methods.update((method.name, method) for method in node.body if isinstance(method, ast.FunctionDef))
    return methods


def flash_calls(method):
    return [node for node in ast.walk(method) if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Attribute)
            and node.func.value.attr == 'flashObject']


def validate(root=ROOT):
    client = root / 'source/scripts/client/Driftkings'
    classes, contracts, errors = {}, {}, []
    for path in (client / 'meta/battle').glob('*.py'):
        for node in ast.parse(path.read_text(encoding='utf-8-sig')).body:
            if not isinstance(node, ast.ClassDef):
                continue
            classes[node.name] = node
            for item in node.body:
                if isinstance(item, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'FLASH_CLASS' for t in item.targets):
                    contracts[node.name] = ast.literal_eval(item.value)
    if not contracts:
        raise ValueError('No Flash meta contracts found')
    as_sources = {}
    for folder in ('flash_source/battle/src', 'flash_source/shared/as3'):
        for path in (root / folder).rglob('*.as'):
            text = path.read_text(encoding='utf-8-sig')
            package = re.search(r'package\s*([\w.]*)\s*\{', text).group(1)
            as_sources[(package + '.' if package else '') + path.stem] = text

    def as_contract(name):
        text = as_sources[name]
        parent = re.search(r'public class \w+ extends (\w+)', text)
        methods, callbacks = {}, set()
        if parent:
            inherited = next((key for key in as_sources if key.endswith('.' + parent.group(1))), None)
            if inherited:
                methods, callbacks = as_contract(inherited)
            elif parent.group(1) == 'BattleUIDisplayable':
                # Native client method; not implemented in our SWF.
                methods['setCompVisible'] = (1, 1)
        for method, args in re.findall(r'public function (\w+)\(([^)]*)\)', text):
            parameters = [arg.strip() for arg in args.split(',') if arg.strip()]
            methods[method] = (sum('=' not in arg for arg in parameters), len(parameters))
        callbacks.update(re.findall(r'public var (\w+)\s*:\s*Function', text))
        return methods, callbacks

    for name, target in sorted(contracts.items()):
        if target not in as_sources:
            errors.append('%s: missing AS class %s' % (name, target))
            continue
        as_methods, callbacks = as_contract(target)
        py_methods = methods_for(name, classes)
        for callback in callbacks:
            if callback not in py_methods:
                errors.append('%s: undeclared Flash callback %s' % (name, callback))
        for method in py_methods.values():
            for call in flash_calls(method):
                called = call.func.attr
                if called not in as_methods:
                    errors.append('%s.%s: missing AS method %s' % (name, method.name, called))
                elif not as_methods[called][0] <= len(call.args) <= as_methods[called][1]:
                    errors.append('%s.%s: argument count differs from AS %s' % (name, method.name, called))
        # Every concrete controller must implement the callbacks declared by AS.
        implementations = []
        for path in (client / 'views/battle').glob('*.py'):
            for node in ast.walk(ast.parse(path.read_text(encoding='utf-8-sig'))):
                if isinstance(node, ast.ClassDef) and any(isinstance(b, ast.Name) and b.id == name for b in node.bases):
                    implementations.append(node)
        if not implementations:
            errors.append('%s: no controller implements this meta' % name)
        for node in implementations:
            combined = dict(classes, **{node.name: node})
            for callback in callbacks:
                method = methods_for(node.name, combined).get(callback)
                if method is None or any(isinstance(n, ast.Name) and n.id == 'NotImplementedError' for n in ast.walk(method)):
                    errors.append('%s: callback %s has no implementation' % (node.name, callback))
    if errors:
        raise ValueError('\n'.join(errors))
    return len(contracts)


if __name__ == '__main__':
    print('Python/Flash contracts: %d components OK' % validate())
