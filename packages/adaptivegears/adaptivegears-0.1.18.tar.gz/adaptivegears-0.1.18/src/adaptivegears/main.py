import sys


def main():
    if len(sys.argv) < 2:
        print("Usage: adaptivegears <command> [options]")
        print("\nAvailable commands:")
        print("  bootstrap    Run bootstrap tool")
        print("  stack        Run stack management tool")
        return 0

    command = sys.argv[1]
    sys.argv = [sys.argv[0]] + sys.argv[2:]

    if command == "bootstrap":
        try:
            from adaptivegears.bootstrap.main import main as bootstrap_main
            return bootstrap_main()
        except ImportError:
            print("Error: Bootstrap module not available.")
            print("Make sure you have installed adaptivegears with the [bootstrap] extra.")
            print("uvx 'adaptivegears[bootstrap]'")
            return 1
    elif command == "stack":
        try:
            from adaptivegears.stack.main import main as stack_main
            return stack_main()
        except ImportError:
            print("Error: Stack module not available.")
            print("Make sure you have installed adaptivegears with the [stack] extra.")
            print("uvx 'adaptivegears[stack]'")
            return 1
    else:
        print(f"Unknown command: {command}")
        print("Usage: adaptivegears <command> [options]")
        return 1

if __name__ == "__main__":
    sys.exit(main())
