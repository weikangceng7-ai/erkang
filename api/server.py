"""/api — your business logic. The ONLY place a contributor writes real code.

`say_hi()` is a small working example (exposed by the MCP server in /mcp_server).
Replace the placeholder `run()` below with your agent's real logic.
"""
from datetime import datetime


def say_hi() -> str:
    """Working example: greet with the server's timezone and current time."""
    now = datetime.now().astimezone()
    tz = now.tzname() or "unknown timezone"
    return f"hello from {tz} {now:%Y-%m-%d %H:%M:%S}: hi"


def run(payload: str = "ping") -> str:
    """Placeholder entrypoint — replace with your agent's real logic."""
    if payload == "error":
        raise RuntimeError("simulated error: something went wrong")
    return f"TODO: implement your agent. You sent: {payload}"


def calculate(expression: str) -> str:
    """Simple calculator: evaluate a math expression and return the result."""
    import ast
    import operator

    ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }

    def _eval(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            op_type = type(node.op)
            if op_type in ops:
                return ops[op_type](left, right)
            raise ValueError(f"Unsupported operator: {op_type}")
        if isinstance(node, ast.UnaryOp):
            operand = _eval(node.operand)
            op_type = type(node.op)
            if op_type in ops:
                return ops[op_type](operand)
            raise ValueError(f"Unsupported unary operator: {op_type}")
        raise ValueError(f"Invalid expression: {ast.dump(node)}")

    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval(tree.body)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error evaluating '{expression}': {e}"
