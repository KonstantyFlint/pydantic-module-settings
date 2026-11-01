import ast
import contextlib
import sys
import types
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec, PathFinder, SourceFileLoader
from typing import Any

from pydantic_env_settings import evaluate


@dataclass(frozen=True)
class LoadOptions:
    prefix: str
    empty_as_unset: bool


@contextlib.contextmanager
def env_settings(
    package: str, prefix: str = "", *, empty_as_unset: bool
) -> Iterator[None]:
    """Load submodules of `package` as env settings for the `with` body.

    Whatever else those submodules import stays untouched. A setting `ABC` is read
    from the environment variable `{prefix}ABC`. With `empty_as_unset`, a variable
    set to an empty string counts as not set, otherwise its value is the empty
    string.

    Raises RuntimeError if a submodule was already imported in any other way, like
    a regular import or different options, as Python would reuse it as it is.
    """
    finder = EnvSettingsFinder(package, LoadOptions(prefix, empty_as_unset))
    finder.ensure_not_imported()
    sys.meta_path.insert(0, finder)
    try:
        yield
    finally:
        sys.meta_path.remove(finder)


class SettingInjector(ast.NodeTransformer):
    """Rewrites annotated module-level names, leaving function and class bodies."""

    def __init__(self, options: LoadOptions) -> None:
        self.options = options

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AnnAssign:
        if isinstance(node.target, ast.Name):
            args = [ast.Constant(self.options.prefix + node.target.id), node.annotation]
            if node.value is not None:
                args.append(node.value)
            node.value = ast.Call(
                ast.Name("__get_setting_value__", ast.Load()),
                args,
                [
                    ast.keyword(
                        "empty_as_unset", ast.Constant(self.options.empty_as_unset)
                    )
                ],
            )
        return node

    def _skip(self, node: ast.AST) -> ast.AST:
        return node

    visit_FunctionDef = visit_AsyncFunctionDef = visit_ClassDef = _skip


class EnvSettingLoader(SourceFileLoader):
    def __init__(self, fullname: str, path: str, options: LoadOptions) -> None:
        super().__init__(fullname, path)
        self.options = options

    def exec_module(self, module: types.ModuleType) -> None:
        module.__dict__["__get_setting_value__"] = evaluate.get_setting_value
        super().exec_module(module)

    def get_code(self, fullname: str) -> types.CodeType:
        # Skip __pycache__: it is shared with regular imports, which would
        # otherwise read and write bytecode meant for the other kind of import.
        path = self.get_filename(fullname)
        return self.source_to_code(self.get_data(path), path)

    # The stubs declare a staticmethod, but at runtime SourceLoader's is an instance
    # method, which is what super() needs here.
    def source_to_code(  # type: ignore[override]
        self, data: Any, path: Any, **kwargs: Any
    ) -> types.CodeType:
        tree = SettingInjector(self.options).visit(ast.parse(data, path))
        ast.fix_missing_locations(tree)
        return super().source_to_code(tree, path, **kwargs)


@dataclass(frozen=True)
class EnvSettingsFinder(MetaPathFinder):
    package: str
    options: LoadOptions

    def _in_scope(self, fullname: str) -> bool:
        return fullname.startswith(f"{self.package}.")

    def _imported_differently(self, module: types.ModuleType | None) -> bool:
        loader = getattr(getattr(module, "__spec__", None), "loader", None)
        if isinstance(loader, EnvSettingLoader):
            return loader.options != self.options
        # Other loaders, like namespace packages', are never replaced by the finder.
        return isinstance(loader, SourceFileLoader)

    def ensure_not_imported(self) -> None:
        imported = sorted(
            name
            for name, module in list(sys.modules.items())
            if self._in_scope(name) and self._imported_differently(module)
        )
        if imported:
            raise RuntimeError(
                f"Settings were already imported differently: {', '.join(imported)}."
            )

    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None,
        target: types.ModuleType | None = None,
    ) -> ModuleSpec | None:
        if not self._in_scope(fullname):
            return None

        spec = PathFinder.find_spec(fullname, path, target)
        if spec and isinstance(spec.loader, SourceFileLoader):
            spec.loader = EnvSettingLoader(fullname, spec.loader.path, self.options)
            return spec

        return None
