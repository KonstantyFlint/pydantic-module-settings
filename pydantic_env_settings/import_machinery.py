import typing

if typing.TYPE_CHECKING:
    import _ast
    import importlib.abc
    from importlib._bootstrap import ModuleSpec
    from importlib.resources.abc import StrPath

    from _typeshed import ReadableBuffer

import ast
import contextlib
import importlib.machinery
import sys
import types
from collections.abc import Iterator, Sequence
from importlib.machinery import SourceFileLoader
from importlib.abc import MetaPathFinder


from pydantic_env_settings import evaluate


@contextlib.contextmanager
def env_import() -> Iterator[None]:
    f = EnvSettingsFinder()
    sys.meta_path.insert(0, f)
    yield
    sys.meta_path.remove(f)


class EnvSettingLoader(SourceFileLoader):
    def exec_module(self, module: types.ModuleType) -> None:
        module.__dict__["__get_setting_value__"] = evaluate.get_setting_value
        super().exec_module(module)

    def source_to_code(
        self,
        data: "ReadableBuffer | str | _ast.Module | _ast.Expression | _ast.Interactive",
        path: "ReadableBuffer | StrPath",
        *,
        _optimize: int = -1,
    ) -> types.CodeType:
        tree = ast.parse(data, path)

        for node in ast.walk(tree):
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                self.emplace_call(node)

        ast.fix_missing_locations(tree)

        return compile(tree, path, "exec", optimize=_optimize)

    @staticmethod
    def emplace_call(node: ast.AnnAssign) -> None:
        function_args = [
            ast.Constant(value=node.target.id),
            node.annotation,
        ]
        if node.value is not None:
            function_args.append(node.value)
        node.value = ast.Call(
            func=ast.Name(id="__get_setting_value__", ctx=ast.Load()),
            args=function_args,
            keywords=[],
        )


class EnvSettingsFinder(MetaPathFinder):

    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None,
        target: types.ModuleType | None = ...,
    ) -> "ModuleSpec | None":
        spec = importlib.machinery.PathFinder.find_spec(fullname, path, target)

        if spec and isinstance(
            spec.loader, importlib.machinery.SourceFileLoader
        ):
            spec.loader = EnvSettingLoader(fullname, spec.loader.path)
            return spec

        return None
