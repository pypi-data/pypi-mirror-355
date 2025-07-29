import argparse
from arithmetic_jy.arithmetic import add, subtract, multiply, divide

def calculate_entry_point():
    """Entry point for the arithmetic operations command line interface.
    This function parses command line arguments to perform arithmetic operations
    on two numbers based on the specified operation.
    It supports addition, subtraction, multiplication, and division.
    """
    
    parser = argparse.ArgumentParser(description="Perform arithmetic operations on two numbers.")
    parser.add_argument("operation", choices=["add", "subtract", "multiply", "divide"], help="The arithmetic operation to perform.")
    parser.add_argument("a", type=float, help="The first number.")
    parser.add_argument("b", type=float, help="The second number.")

    args = parser.parse_args()

    assert args.operation in ["add", "subtract", "multiply", "divide"], "Invalid operation specified."
    assert isinstance(args.a, (int, float)), "First argument must be a number."
    assert isinstance(args.b, (int, float)), "Second argument must be a number."
    assert args.operation != "divide" or args.b != 0, "Cannot divide by zero."

    if args.operation == "add":
        result = add(args.a, args.b)
    elif args.operation == "subtract":
        result = subtract(args.a, args.b)
    elif args.operation == "multiply":
        result = multiply(args.a, args.b)
    elif args.operation == "divide":
        result = divide(args.a, args.b)

    print(f"Result: {result}")