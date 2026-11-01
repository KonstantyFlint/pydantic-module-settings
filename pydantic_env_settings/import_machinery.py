import ast
import contextlib
import sys
import types
from collections.abc import Iterator, Sequence
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec, PathFinder, SourceFileLoader

from pydantic_env_settings import evaluate


@contextlib.contextmanager
def env_import(package: str, *packages: str) -> Iterator[None]:
    """Load the named modules/packages as env settings for the `with` body.

    Only the named modules and their submodules are rewritten, so settings can
    import each other while everything else they import stays untouched.
    """
    finder = EnvSettingsFinder((package, *packages))
    sys.meta_path.insert(0, finder)
    yield
    sys.meta_path.remove(finder)


class SettingInjector(ast.NodeTransformer):
    """Rewrites annotated names into env lookups."""

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AnnAssign:
        if isinstance(node.target, ast.Name):
            args = [ast.Constant(node.target.id), node.annotation]
            if node.value is not None:
                args.append(node.value)
            node.value = ast.Call(
                ast.Name("__get_setting_value__", ast.Load()), args, []
            )
        return node


class EnvSettingLoader(SourceFileLoader):
    def exec_module(self, module: types.ModuleType) -> None:
        module.__dict__["__get_setting_value__"] = evaluate.get_setting_value
        super().exec_module(module)

    def source_to_code(self, data, path, **kwargs) -> types.CodeType:
        tree = SettingInjector().visit(ast.parse(data, path))
        ast.fix_missing_locations(tree)
        return super().source_to_code(tree, path, **kwargs)


class EnvSettingsFinder(MetaPathFinder):
    def __init__(self, packages: Sequence[str]) -> None:
        self.packages = packages

    def _in_scope(self, fullname: str) -> bool:
        return any(
            fullname == package or fullname.startswith(f"{package}.")
            for package in self.packages
        )

    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None,
        target: types.ModuleType | None = ...,
    ) -> ModuleSpec | None:
        if not self._in_scope(fullname):
            return None

        spec = PathFinder.find_spec(fullname, path, target)
        if spec and isinstance(spec.loader, SourceFileLoader):
            spec.loader = EnvSettingLoader(fullname, spec.loader.path)
            return spec

        return None
