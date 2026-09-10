#!/usr/bin/env python3
"""Inlines src/ into one self-contained dist/*.py per script."""

import ast
import io
import os
import sys
import time
import tokenize

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
DIST = os.path.join(ROOT, "dist")

ENTRIES = [
    {"in": "src/armslore/index.py", "out": "arms-lore"},
    {"in": "src/buffs/index.py", "out": "buffs"},
    {"in": "src/magery/index.py", "out": "magery"},
    {"in": "src/mysticism/index.py", "out": "mysticism"},
    {"in": "src/chivalry/index.py", "out": "chivalry"},
    {"in": "src/taming/index.py", "out": "tame"},
    {"in": "src/mining/index.py", "out": "mining"},
    {"in": "src/mining/here.py", "out": "mine-here"},
    {"in": "src/lumberjacking/index.py", "out": "lumberjack"},
    {"in": "src/fishing/index.py", "out": "fishing"},
    {"in": "src/attack/index.py", "out": "attack"},
    {"in": "src/bowcraft/index.py", "out": "bowcraft"},
    {"in": "src/tinkering/index.py", "out": "tinkering"},
    {"in": "src/carpentry/index.py", "out": "carpentry"},
    {"in": "src/inscription/index.py", "out": "inscription"},
    {"in": "src/bod/index.py", "out": "bod"},
    {"in": "src/inventory/index.py", "out": "inventory"},
]

# Legion strips these from the script it loads and injects API as a builtin, so the artifact
# carries one of each and no module body does.
HOISTED = ("API", "time", "clr", "System", "json")


class BuildError(Exception):
    pass


def read(path):
    handle = open(path, "r")

    try:
        return handle.read()
    finally:
        handle.close()


def rel(path):
    return os.path.relpath(path, ROOT).replace(os.sep, "/")


def parse(path):
    source = read(path)

    try:
        return source, ast.parse(source, filename=rel(path))
    except SyntaxError as error:
        raise BuildError("%s:%s: %s" % (rel(path), error.lineno, error.msg))


def check_language_level(path, source, tree):
    """Rejects what IronPython 3.4.2 cannot parse but the local CPython happily can."""
    bad = []

    def fail(node, what):
        bad.append((getattr(node, "lineno", 0), what))

    def not_34(node, what):
        fail(node, "%s is not Python 3.4" % what)

    top = set(id(node) for node in tree.body)

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)) and id(node) not in top:
            fail(node, "an import below the top level, which the bundle cannot resolve")
        elif isinstance(node, ast.JoinedStr):
            not_34(node, "f-string")
        elif isinstance(node, ast.AnnAssign):
            not_34(node, "variable annotation")
        elif isinstance(node, ast.NamedExpr):
            not_34(node, "walrus operator")
        elif isinstance(node, (ast.AsyncFunctionDef, ast.Await, ast.AsyncFor, ast.AsyncWith)):
            not_34(node, "async/await")
        elif isinstance(node, ast.MatMult):
            not_34(node, "matrix multiply")
        elif isinstance(node, ast.Match):
            not_34(node, "match statement")
        elif isinstance(node, ast.arg) and node.annotation is not None:
            not_34(node, "argument annotation")
        elif isinstance(node, (ast.FunctionDef, ast.Lambda)):
            if getattr(node, "returns", None) is not None:
                not_34(node, "return annotation")
            if getattr(node.args, "posonlyargs", None):
                not_34(node, "positional-only argument")
        elif isinstance(node, ast.Call):
            if len([a for a in node.args if isinstance(a, ast.Starred)]) > 1:
                not_34(node, "PEP 448 call unpacking")
            if len([k for k in node.keywords if k.arg is None]) > 1:
                not_34(node, "PEP 448 call unpacking")
        elif isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            if isinstance(getattr(node, "ctx", None), ast.Load):
                if any(isinstance(e, ast.Starred) for e in node.elts):
                    not_34(node, "PEP 448 display unpacking")
        elif isinstance(node, ast.Dict):
            if any(key is None for key in node.keys):
                not_34(node, "PEP 448 dict unpacking")

    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.NUMBER and "_" in token.string:
            bad.append((token.start[0], "underscore in a numeric literal is not Python 3.4"))

    if bad:
        lines = ["%s:%d: %s" % (rel(path), line, what) for line, what in sorted(set(bad))]
        raise BuildError("\n".join(lines))


def imports_of(path, tree):
    """The modules this one pulls in, and the line spans every import statement occupies."""
    folder = os.path.dirname(path)
    deps = []
    spans = []
    hoisted = set()

    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name not in HOISTED:
                    raise BuildError("%s:%d: import %s - only %s may be imported outright"
                                     % (rel(path), node.lineno, alias.name, " and ".join(HOISTED)))

                hoisted.add(alias.name)

            spans.append((node.lineno, node.end_lineno))
            continue

        if not isinstance(node, ast.ImportFrom):
            continue

        for alias in node.names:
            if alias.name == "*":
                raise BuildError("%s:%d: `import *` hides what the bundle needs; name the imports"
                                 % (rel(path), node.lineno))

            if alias.asname is not None:
                raise BuildError("%s:%d: `as %s` cannot survive a flat namespace; rename at the source"
                                 % (rel(path), node.lineno, alias.asname))

        if node.level > 1:
            raise BuildError("%s:%d: only one leading dot is resolvable" % (rel(path), node.lineno))

        if node.level == 1:
            if node.module is None:
                raise BuildError("%s:%d: `from . import x` has no file to name" % (rel(path), node.lineno))

            deps.append((os.path.join(folder, node.module.replace(".", os.sep) + ".py"),
                         [a.name for a in node.names], node.lineno))
        elif node.module in HOISTED:
            hoisted.add(node.module)
        else:
            deps.append((os.path.join(SRC, node.module.replace(".", os.sep) + ".py"),
                         [a.name for a in node.names], node.lineno))

        spans.append((node.lineno, node.end_lineno))

    return deps, spans, hoisted


def defines(node):
    """The single top-level name a statement defines, or None if it is a statement to run."""
    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
        return node.name

    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        if isinstance(node.targets[0], ast.Name):
            return node.targets[0].id

    return None


def mentions(node):
    """Every bare name under a statement. An over-approximation, so shaking can only keep too much."""
    return set(child.id for child in ast.walk(node) if isinstance(child, ast.Name))


def chunks_of(path, source, tree, import_lines):
    """Top-level statements as (name, mentions, text), each carrying the comments written above it."""
    lines = source.split("\n")
    found = []
    claimed = min(import_lines) - 1 if import_lines else 0

    for node in tree.body:
        if node.lineno in import_lines:
            claimed = max(claimed, node.end_lineno)
            continue

        start = node.lineno

        while start - 1 > claimed and lines[start - 2].lstrip().startswith("#"):
            start -= 1

        gap = 0

        while start - 1 - gap > claimed and not lines[start - 2 - gap].strip():
            gap += 1

        text = "\n".join(lines[start - 1:node.end_lineno]).strip("\n")
        claimed = max(claimed, node.end_lineno)

        if text:
            found.append((defines(node), mentions(node), text, min(gap, 2)))

    return found


def shake(modules, entry_path):
    """Drops the definitions no reachable code names, so an artifact carries only what it runs."""
    owner = {}

    for path, chunks in modules:
        for name, _uses, _text, _gap in chunks:
            if name is not None and path != entry_path:
                owner.setdefault(name, (path, name))

    wanted = set()
    pending = []

    for path, chunks in modules:
        for name, uses, _text, _gap in chunks:
            # Everything in the entry is the script itself, and a bare statement anywhere runs
            if path == entry_path or name is None:
                pending.append(uses)

    while pending:
        for used in pending.pop():
            if used in owner and used not in wanted:
                wanted.add(used)

                for path, chunks in modules:
                    for name, uses, _text, _gap in chunks:
                        if name == used and path != entry_path:
                            pending.append(uses)

    kept = []

    for path, chunks in modules:
        keeping = [(text, gap) for name, _uses, text, gap in chunks
                   if path == entry_path or name is None or name in wanted]

        if keeping:
            kept.append((path, keeping))

    return kept


def bound_names(tree):
    names = set()

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
                elif isinstance(target, (ast.Tuple, ast.List)):
                    names.update(e.id for e in target.elts if isinstance(e, ast.Name))

    return names


def collect(entry_path):
    """Every module reachable from the entry, deepest first, each visited once."""
    ordered = []
    needed = set()
    provided = {}
    seen = set()
    stack = []

    def visit(path):
        path = os.path.normpath(path)

        if path in seen:
            return provided[path]

        if path in stack:
            cycle = " -> ".join(rel(p) for p in stack[stack.index(path):] + [path])
            raise BuildError("import cycle: %s" % cycle)

        if not os.path.exists(path):
            raise BuildError("%s imports %s, which does not exist" % (rel(stack[-1]), rel(path)))

        stack.append(path)
        source, tree = parse(path)
        check_language_level(path, source, tree)
        deps, spans, hoisted = imports_of(path, tree)
        needed.update(hoisted)

        for dep, names, lineno in deps:
            exported = visit(dep)
            missing = [name for name in names if name not in exported]

            if missing:
                raise BuildError("%s:%d: %s does not define %s"
                                 % (rel(path), lineno, rel(dep), ", ".join(sorted(missing))))

        stack.pop()
        seen.add(path)
        # What a module re-exports counts as provided: the bundle is flat, so a config that pulls a
        # shared constant through still answers for it
        names = bound_names(tree) | set(name for _dep, imported, _line in deps for name in imported)
        provided[path] = names
        ordered.append((path, chunks_of(path, source, tree, set(start for start, _end in spans))))

        return names

    visit(entry_path)

    return ordered, needed


def bundle(entry):
    entry_path = os.path.normpath(os.path.join(ROOT, entry["in"]))
    modules, needed = collect(entry_path)

    owner = {}

    for path, chunks in modules:
        for name, _uses, _text, _gap in chunks:
            if name is None:
                continue

            if name in owner:
                raise BuildError("%s and %s both define `%s` at the top level"
                                 % (rel(owner[name]), rel(path), name))

            owner[name] = path

    head = "# Built from %s by build.py - do not edit.\n\n" % entry["in"]
    head += "\n".join("import " + name for name in HOISTED if name in needed)

    blocks = [head.rstrip("\n")]

    for path, texts in shake(modules, entry_path):
        piece = "# " + rel(path)

        for index, (text, gap) in enumerate(texts):
            piece += ("\n" * (gap + 1) if index else "\n") + text

        blocks.append(piece)

    output = "\n\n\n".join(blocks) + "\n"

    try:
        ast.parse(output)
    except SyntaxError as error:
        raise BuildError("%s: the bundle does not parse at line %s: %s"
                         % (entry["out"], error.lineno, error.msg))

    return output


def build_one(entry):
    output = bundle(entry)
    target = os.path.join(DIST, entry["out"] + ".py")

    if not os.path.isdir(DIST):
        os.makedirs(DIST)

    if os.path.exists(target) and read(target) == output:
        return target, False

    handle = open(target, "w")

    try:
        handle.write(output)
    finally:
        handle.close()

    return target, True


def build_all():
    failures = 0

    for entry in ENTRIES:
        try:
            target, changed = build_one(entry)
            print("  %s%s" % (rel(target), "" if changed else " (unchanged)"))
        except BuildError as error:
            failures += 1
            print("  %s FAILED" % entry["out"])
            print("    " + str(error).replace("\n", "\n    "))

    return failures


def sources():
    found = []

    for folder, _dirs, files in os.walk(SRC):
        for name in files:
            if name.endswith(".py"):
                found.append(os.path.join(folder, name))

    return found


def watch():
    print("watching %s" % rel(SRC))
    stamps = {}

    while True:
        current = {}

        for path in sources():
            try:
                current[path] = os.path.getmtime(path)
            except OSError:
                pass

        if current != stamps:
            stamps = current
            build_all()

        time.sleep(0.3)


def main():
    if "--watch" in sys.argv[1:]:
        watch()
        return 0

    print("building %d script%s" % (len(ENTRIES), "" if len(ENTRIES) == 1 else "s"))

    return 1 if build_all() else 0


if __name__ == "__main__":
    sys.exit(main())
