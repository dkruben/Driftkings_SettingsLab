"""Retain real settings imports when testing isolated gameplay AST bodies."""
import ast
from pathlib import Path

CLIENT = Path(__file__).resolve().parents[2] / 'source/scripts/client/Driftkings'


def settings_globals(namespace, *modules):
    for module in modules:
        path = CLIENT / (module.replace('.', '/') + '.py')
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        tree.body = [node for node in tree.body if isinstance(node, ast.ImportFrom)
                     and node.module in ('Driftkings._constants', 'Driftkings.settings.service')]
        exec(compile(tree, str(path), 'exec'), namespace)
