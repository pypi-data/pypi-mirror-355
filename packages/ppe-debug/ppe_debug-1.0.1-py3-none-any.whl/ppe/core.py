import ast
import inspect
import textwrap
from typing import Any, Callable


class PPETransformer(ast.NodeTransformer):
    """AST transformer that adds debug print statements based on comments."""

    def __init__(self, source_lines):
        self.source_lines = source_lines

    def visit_stmt_with_comment(self, node, line_no):
        """Check if a statement has a PPE comment and transform accordingly."""
        if line_no <= len(self.source_lines):
            line = self.source_lines[line_no - 1].strip()

            # Look for ## comments
            if '##' in line:
                comment_part = line.split('##', 1)[1].strip()

                if comment_part == '-':
                    # Case 2: Print the statement itself
                    stmt_text = line.split('##')[0].strip()
                    print_node = ast.Expr(
                        value=ast.Call(
                            func=ast.Name(id='print', ctx=ast.Load()),
                            args=[ast.Constant(value=f"PPE: {stmt_text}")],
                            keywords=[]
                        )
                    )
                    return [print_node, node]

                elif comment_part.startswith('@'):
                    # Case 3: Variable value inspection
                    return self.handle_variable_inspection(node, comment_part)

                elif comment_part:
                    # Case 1: Print the comment string
                    print_node = ast.Expr(
                        value=ast.Call(
                            func=ast.Name(id='print', ctx=ast.Load()),
                            args=[ast.Constant(value=f"PPE: {comment_part}")],
                            keywords=[]
                        )
                    )
                    return [print_node, node]

        return node

    def handle_variable_inspection(self, node, comment_part):
        """Handle variable inspection comments like @var1,var2 or @before:var1,var2"""
        # Parse the comment: @var1,var2 or @before:var1,var2 or @after:var1,var2
        inspection_part = comment_part[1:]  # Remove '@'

        # Check for before/after prefix
        print_before = False
        if inspection_part.startswith('before:'):
            print_before = True
            var_part = inspection_part[7:]  # Remove 'before:'
        elif inspection_part.startswith('after:'):
            print_before = False
            var_part = inspection_part[6:]  # Remove 'after:'
        else:
            # Default behavior: print after
            print_before = False
            var_part = inspection_part

        # Parse variable names
        var_names = [v.strip() for v in var_part.split(',') if v.strip()]

        if not var_names:
            return node

        # Create the variable inspection print statement
        print_node = self.create_variable_inspection_print(var_names, print_before)

        if print_before:
            return [print_node, node]  # Print before execution
        else:
            return [node, print_node]  # Print after execution (default)

    def create_variable_inspection_print(self, var_names, print_before=False):
        """Create a try-catch print statement for variable inspection"""

        # Build the JoinedStr (f-string) AST node
        if print_before:
            joined_str_values = [ast.Constant(value="PPE: [Before] ")]
        else:
            joined_str_values = [ast.Constant(value="PPE: [After] ")]

        for i, var in enumerate(var_names):
            if i > 0:
                joined_str_values.append(ast.Constant(value=", "))
            joined_str_values.append(ast.Constant(value=f"{var}="))
            joined_str_values.append(ast.FormattedValue(
                value=ast.Name(id=var, ctx=ast.Load()),
                conversion=-1,
                format_spec=None
            ))

        # Create the try block with print statement
        try_body = [
            ast.Expr(
                value=ast.Call(
                    func=ast.Name(id='print', ctx=ast.Load()),
                    args=[ast.JoinedStr(values=joined_str_values)],
                    keywords=[]
                )
            )
        ]

        # Create the except block for error handling
        except_body = [
            ast.Expr(
                value=ast.Call(
                    func=ast.Name(id='print', ctx=ast.Load()),
                    args=[ast.Constant(value="PPE: Variable inspection failed")],
                    keywords=[]
                )
            )
        ]

        # Return the complete try-except statement
        return ast.Try(
            body=try_body,
            handlers=[
                ast.ExceptHandler(
                    type=ast.Name(id='NameError', ctx=ast.Load()),
                    name=None,
                    body=except_body
                )
            ],
            orelse=[],
            finalbody=[]
        )

    def visit_Assign(self, node):
        """Transform assignment statements."""
        result = self.visit_stmt_with_comment(node, node.lineno)
        if isinstance(result, list):
            return result
        return self.generic_visit(node)

    def visit_AnnAssign(self, node):
        """Transform annotated assignment statements."""
        result = self.visit_stmt_with_comment(node, node.lineno)
        if isinstance(result, list):
            return result
        return self.generic_visit(node)

    def visit_AugAssign(self, node):
        """Transform augmented assignment statements (+=, -=, etc.)."""
        result = self.visit_stmt_with_comment(node, node.lineno)
        if isinstance(result, list):
            return result
        return self.generic_visit(node)

    def visit_Expr(self, node):
        """Transform expression statements."""
        result = self.visit_stmt_with_comment(node, node.lineno)
        if isinstance(result, list):
            return result
        return self.generic_visit(node)

    def visit_If(self, node):
        """Transform if statements."""
        result = self.visit_stmt_with_comment(node, node.lineno)
        if isinstance(result, list):
            return result
        return self.generic_visit(node)

    def visit_For(self, node):
        """Transform for loops."""
        result = self.visit_stmt_with_comment(node, node.lineno)
        if isinstance(result, list):
            return result
        return self.generic_visit(node)

    def visit_While(self, node):
        """Transform while loops."""
        result = self.visit_stmt_with_comment(node, node.lineno)
        if isinstance(result, list):
            return result
        return self.generic_visit(node)

    def visit_Return(self, node):
        """Transform return statements."""
        result = self.visit_stmt_with_comment(node, node.lineno)
        if isinstance(result, list):
            return result
        return self.generic_visit(node)

    def visit_Break(self, node):
        """Transform break statements."""
        result = self.visit_stmt_with_comment(node, node.lineno)
        if isinstance(result, list):
            return result
        return self.generic_visit(node)

    def visit_Continue(self, node):
        """Transform continue statements."""
        result = self.visit_stmt_with_comment(node, node.lineno)
        if isinstance(result, list):
            return result
        return self.generic_visit(node)


def ppe_debug(func: Callable) -> Callable:
    """
    Decorator that enables PPE debugging for a function.

    Usage:
        @ppe_debug
        def my_function():
            a = 5  ## Initialize variable a
            b = 10 ## Initialize variable b
            c = a + b  ## -
            return c
    """

    def wrapper(*args, **kwargs):
        # Get the source code of the function
        source = inspect.getsource(func)
        source = textwrap.dedent(source)

        # Remove the decorator line
        lines = source.split('\n')
        filtered_lines = []
        skip_decorator = True

        for line in lines:
            if skip_decorator and line.strip().startswith('@'):
                continue
            elif skip_decorator and line.strip().startswith('def'):
                skip_decorator = False
                filtered_lines.append(line)
            elif not skip_decorator:
                filtered_lines.append(line)

        modified_source = '\n'.join(filtered_lines)
        source_lines = modified_source.split('\n')

        # Parse the AST
        tree = ast.parse(modified_source)

        # Transform the AST
        transformer = PPETransformer(source_lines)
        new_tree = transformer.visit(tree)

        # Fix missing locations
        ast.fix_missing_locations(new_tree)

        # Compile and execute
        code = compile(new_tree, f"<PPE:{func.__name__}>", 'exec')

        # Create execution environment
        func_globals = func.__globals__.copy()
        func_locals = {}

        # Add function arguments to locals
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        func_locals.update(bound_args.arguments)

        # Execute the transformed code
        namespace = func_globals.copy()
        namespace.update(func_locals)

        exec(code, namespace)

        # Get the transformed function and call it
        transformed_func = namespace[func.__name__]
        return transformed_func(*args, **kwargs)

    return wrapper
