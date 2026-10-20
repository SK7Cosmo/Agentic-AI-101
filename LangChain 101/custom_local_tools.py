from langchain_core.tools import tool

@tool
def add(a: float, b: float) -> float:
    """
    Add two numbers together.
    The agent will use this when it detects an addition problem.
    """
    return a + b


@tool
def subtract(a: float, b: float) -> float:
    """
    Subtract two numbers together.
    The agent will use this when it detects a subtraction problem.
    """
    return a - b


@tool
def multiply(a: float, b: float) -> float:
    """
    Multiply two numbers together.
    The agent will use this when it detects a multiplication problem.
    """
    return a * b


@tool
def divide(a: float, b: float) -> str:
    """
    Divide the first number by the second.
    Includes error handling for division by zero.
    """
    if b == 0:
        return "Error: Cannot divide by zero"
    return str(a / b)
