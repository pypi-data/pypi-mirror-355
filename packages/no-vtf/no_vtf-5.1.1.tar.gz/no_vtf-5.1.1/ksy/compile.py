#!/usr/bin/env python3

# SPDX-FileCopyrightText: b5327157 <b5327157@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import ast
import enum
import pathlib
import subprocess

from collections import defaultdict
from enum import Enum
from typing import NoReturn, Optional, TypeVar


def main() -> None:
    vtf_input = pathlib.Path("ksy/vtf.ksy")
    vtf_output = pathlib.Path("no_vtf/vtf/generated/parser.py")

    compile_ksy(vtf_input, vtf_output)
    adjust_py(vtf_output)


def compile_ksy(input_ksy: pathlib.Path, output_py: pathlib.Path) -> None:
    subprocess.run(
        [
            "kaitai-struct-compiler",
            "--target=python",
            "--outdir",
            str(output_py.parent),
            str(input_ksy),
        ],
        check=True,
    )
    pathlib.Path(output_py.parent, f"{input_ksy.stem}.py").rename(output_py)


def adjust_py(inout_py: pathlib.Path) -> None:
    source = inout_py.read_text()
    tree_in: ast.AST = ast.parse(source, inout_py)

    tree_out = ClassUnnester().visit(tree_in)
    assert tree_out  # noqa S101 type narrowing

    source = ast.unparse(tree_out)
    inout_py.write_text(source + "\n")


class ClassUnnester(ast.NodeTransformer):
    class State(Enum):
        NONE = enum.auto()
        UNNESTING = enum.auto()
        UPDATING_REFERENCES = enum.auto()

    def __init__(self) -> None:
        self._state = ClassUnnester.State.NONE

        self._class_tree: Tree[str] = Tree()
        self._unnested_classes: list[ast.ClassDef] = []

        self._class_stack: list[ast.ClassDef] = []
        self._attribute_stack: list[ast.Attribute] = []

        self._collapse_attributes_depth = 0

        self._check_post_conditions()

    def visit(self, node: ast.AST) -> Optional[ast.AST]:
        if self._state is not ClassUnnester.State.NONE:
            node_optional: Optional[ast.AST] = super().visit(node)
            return node_optional

        self._state = ClassUnnester.State.UNNESTING
        node = super().visit(node)

        self._state = ClassUnnester.State.UPDATING_REFERENCES
        node = super().visit(node)

        self._state = ClassUnnester.State.NONE
        self._class_tree = Tree()
        self._unnested_classes = []
        self._check_post_conditions()

        return node

    def visit_Module(self, node: ast.Module) -> Optional[ast.AST]:  # noqa: N802
        node_generic: Optional[ast.AST] = self.generic_visit(node)

        if self._state is ClassUnnester.State.UNNESTING:
            node_generic = self._post_visit_Module_UNNESTING(node_generic)

        return node_generic

    def visit_ClassDef(self, node: ast.ClassDef) -> Optional[ast.AST]:  # noqa: N802
        if self._state is ClassUnnester.State.UNNESTING:
            node = self._pre_visit_ClassDef_UNNESTING(node)

        self._class_stack.append(node)
        node_generic: Optional[ast.AST] = self.generic_visit(node)
        self._class_stack.pop()

        if self._state is ClassUnnester.State.UNNESTING:
            node_generic = self._post_visit_ClassDef_UNNESTING(node_generic)

        return node_generic

    def visit_Attribute(self, node: ast.Attribute) -> Optional[ast.AST]:  # noqa: N802
        self._attribute_stack.append(node)
        node_generic: Optional[ast.AST] = self.generic_visit(node)
        self._attribute_stack.pop()

        if self._state is ClassUnnester.State.UPDATING_REFERENCES:
            node_generic = self._post_visit_Attribute_UPDATING_REFERENCES(node_generic)

        return node_generic

    def visit_Name(self, node: ast.Name) -> Optional[ast.AST]:  # noqa: N802
        if self._state is ClassUnnester.State.UPDATING_REFERENCES:
            node = self._pre_visit_Name_UPDATING_REFERENCES(node)

        node_generic: Optional[ast.AST] = self.generic_visit(node)
        return node_generic

    def _pre_visit_ClassDef_UNNESTING(self, node: ast.ClassDef) -> ast.ClassDef:  # noqa: N802
        class_tree = self._class_tree
        for class_stack_node in self._class_stack:
            class_tree = class_tree[class_stack_node.name]
        class_tree[node.name]

        if self._class_stack:
            self._unnested_classes.append(node)

        return node

    def _post_visit_ClassDef_UNNESTING(  # noqa: N802
        self, node: Optional[ast.AST]
    ) -> Optional[ast.AST]:
        if isinstance(node, ast.ClassDef) and self._class_stack:
            node.name = (
                "".join(class_stack_node.name for class_stack_node in self._class_stack) + node.name
            )
            return None

        return node

    def _post_visit_Module_UNNESTING(  # noqa: N802
        self, node: Optional[ast.AST]
    ) -> Optional[ast.AST]:
        assert isinstance(node, ast.Module)  # noqa S101 type narrowing

        for unnested_class in self._unnested_classes:
            node.body.append(unnested_class)

        return node

    def _pre_visit_Name_UPDATING_REFERENCES(self, node: ast.Name) -> ast.Name:  # noqa: N802
        path = [node.id] + [node.attr for node in reversed(self._attribute_stack)]

        longest_match: list[str] = []
        class_tree = self._class_tree
        for path_component in path:
            if path_component not in class_tree:
                break

            longest_match.append(path_component)
            class_tree = class_tree[path_component]

        if longest_match:
            assert not self._collapse_attributes_depth  # noqa S101 debug check
            self._collapse_attributes_depth = len(longest_match) - 1
            assert (  # noqa S101 debug check
                len(self._attribute_stack) >= self._collapse_attributes_depth
            )

            node.id = "".join(longest_match)

        return node

    def _post_visit_Attribute_UPDATING_REFERENCES(  # noqa: N802
        self, node: Optional[ast.AST]
    ) -> Optional[ast.AST]:
        if self._collapse_attributes_depth:
            assert isinstance(node, ast.Attribute)  # noqa S101 type narrowing
            node = node.value
            self._collapse_attributes_depth -= 1

        return node

    def _check_post_conditions(self) -> None:
        assert self._state is ClassUnnester.State.NONE  # noqa S101 debug check
        assert not self._class_tree  # noqa S101 debug check
        assert not self._unnested_classes  # noqa S101 debug check
        assert not self._class_stack  # noqa S101 debug check
        assert not self._attribute_stack  # noqa S101 debug check
        assert not self._collapse_attributes_depth  # noqa S101 debug check

    def visit_Expression(self, node: ast.Expression) -> ast.AST:  # noqa: N802
        self._report_unsupported(node)

    def visit_Interactive(self, node: ast.Interactive) -> ast.AST:  # noqa: N802
        self._report_unsupported(node)

    def visit_FunctionType(self, node: ast.FunctionType) -> ast.AST:  # noqa: N802
        self._report_unsupported(node)

    def _report_unsupported(self, node: ast.AST) -> NoReturn:
        raise ValueError(f"{type(node).__name__} root node is not supported")


_TreeNode = TypeVar("_TreeNode")


class Tree(defaultdict[_TreeNode, "Tree[_TreeNode]"]):
    def __init__(self) -> None:
        super().__init__(Tree)


if __name__ == "__main__":
    main()
