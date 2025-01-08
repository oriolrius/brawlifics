import ast
import operator
import random
from PIL import Image
from io import BytesIO
from typing import Union, Dict
from brawlifics.lib.logger import logger


# Supported mathematical operations
OPERATORS: Dict[type, callable] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


def get_first_frame(file_path: str):
    try:
        # Open the GIF and get first frame
        with Image.open(file_path) as img:
            first_frame = img.convert("RGBA")
            # Save first frame to BytesIO buffer
            buffer = BytesIO()
            first_frame.save(buffer, format="PNG")
            buffer.seek(0)
            return buffer.getvalue()
    except FileNotFoundError:
        raise ValueError(f"File not found: {file_path}")


def safe_eval(expression: str) -> Union[int, float]:
    """
    Safely evaluate a simple mathematical expression.
    Only allows basic arithmetic operations (+, -, *, /) and numbers.

    Args:
        expression (str): A mathematical expression as string (e.g., "2 + 3")

    Returns:
        Union[int, float]: The result of the evaluation

    Raises:
        ValueError: If the expression is invalid or contains unauthorized operations
    """
    try:
        # Parse the expression into an AST
        tree = ast.parse(expression, mode="eval")

        def evaluate(node):
            # Numbers
            if isinstance(node, ast.Constant):
                return node.value
            # Mathematical operations
            elif isinstance(node, ast.BinOp):
                # Get the operation from our supported operators
                op = type(node.op)
                if op not in OPERATORS:
                    raise ValueError(f"Unsupported operation: {op}")
                # Recursively evaluate the left and right parts
                left = evaluate(node.left)
                right = evaluate(node.right)
                # Perform the operation
                return OPERATORS[op](left, right)
            # Expression wrapper
            elif isinstance(node, ast.Expression):
                return evaluate(node.body)
            else:
                raise ValueError(f"Unsupported syntax: {type(node)}")

        result = evaluate(tree)
        return result

    except Exception as e:
        logger.error(f"Error evaluating expression '{expression}': {str(e)}")
        raise ValueError(f"Invalid expression: {expression}")


def generate_challenge() -> str:
    """
    Generate a random mathematical challenge.
    Currently supports addition only, but can be extended for other operations.

    Returns:
        str: A mathematical expression as string
    """
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    return f"{num1} + {num2}"


def extract_player_id(topic: str) -> str:
    """
    Extract player ID from an MQTT topic.
    Expected format: 'brawlifics/player/<player_id>/...'

    Args:
        topic (str): The MQTT topic string

    Returns:
        str: The extracted player ID

    Raises:
        ValueError: If the topic format is invalid
    """
    try:
        parts = topic.split("/")
        if len(parts) >= 3 and parts[0] == "brawlifics" and parts[1] == "player":
            return parts[2]
        raise ValueError("Invalid topic format")
    except Exception as e:
        logger.error(f"Error extracting player ID from topic '{topic}': {str(e)}")
        raise ValueError(f"Invalid topic format: {topic}")


def validate_player_name(name: str) -> bool:
    """
    Validate a player name.

    Args:
        name (str): The player name to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not name or not isinstance(name, str):
        return False
    # Add any additional validation rules here
    return True


def generate_game_id() -> str:
    """
    Generate a random game ID. It's a 3-digit number between 000 and 999.

    Returns:
        str: A 3-digit game ID
    """
    return str(random.randint(0, 999)).zfill(3)


# Test the utilities if run directly
if __name__ == "__main__":
    # Test safe_eval
    assert safe_eval("2 + 3") == 5
    assert safe_eval("10 - 5") == 5
    assert safe_eval("3 * 4") == 12
    assert safe_eval("8 / 2") == 4.0

    # Test generate_challenge
    challenge = generate_challenge()
    assert "+" in challenge

    # Test extract_player_id
    assert extract_player_id("brawlifics/player/player1/challenge") == "player1"

    print("All tests passed!")
