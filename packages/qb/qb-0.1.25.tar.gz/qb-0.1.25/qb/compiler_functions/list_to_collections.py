import ast

from ..qbstd.types import collection


class ListTransformer(ast.NodeTransformer):
    def visit_List(self, node):
        return ast.Call(
            func=ast.Attribute(
                value=ast.Name(id='collection', ctx=ast.Load()),
                attr='of',
                ctx=ast.Load()
            ),
            args=[node],
            keywords=[]
        )


def transform_lists(code: str) -> str:
    tree = ast.parse(code)

    ListTransformer().visit(tree)
    ast.fix_missing_locations(tree)

    return ast.unparse(tree)
