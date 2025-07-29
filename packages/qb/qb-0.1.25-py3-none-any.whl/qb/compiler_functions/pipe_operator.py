import ast


class PipeTransformer(ast.NodeTransformer):
    def visit_BinOp(self, node):
        if isinstance(node.op, ast.RShift):
            # Recursive call for the left node if it's also a BinOp
            left = self.visit(node.left) if isinstance(node.left, ast.BinOp) else node.left
            # Ensure that the right node is a function
            if isinstance(node.right, ast.Call):
                node.right.args.append(left)
                return node.right
            elif isinstance(node.right, ast.expr):  # Change here
                return ast.Call(func=node.right, args=[left], keywords=[])
            else:
                raise TypeError(get_pipe_error_text("right"))
        
        if isinstance(node.op, ast.LShift):
            # Recursive call for the right node if it's also a BinOp
            right = self.visit(node.right) if isinstance(node.right, ast.BinOp) else node.right
            # Ensure that the left node is a function
            if isinstance(node.left, ast.Call):
                node.left.args.append(right)
                return node.left
            elif isinstance(node.left, ast.expr):  # Change here
                return ast.Call(func=node.left, args=[right], keywords=[])
            else:
                raise TypeError(get_pipe_error_text("left"))
        
        return self.generic_visit(node)

def manage_pipes(code: str) -> str:
    tree = ast.parse(code)
    PipeTransformer().visit(tree)
    ast.fix_missing_locations(tree)

    return ast.unparse(tree)

def get_pipe_error_text(side: str) -> str:
    op = "|>" if side == "right" else "<|"
    error = f"The {side} operand of the '{op}' operator must be a function"
    return error