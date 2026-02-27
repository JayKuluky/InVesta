"""
Main entry point for InVesta application.
Runs the Streamlit web application.
"""

import subprocess
import sys


def main() -> None:
    """
    Run the InVesta Streamlit application.
    
    This function serves as the main entry point for the application.
    It launches the Streamlit server with the app.py file.
    """
    try:
        # Run Streamlit app
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "app.py"],
            check=False
        )
    except KeyboardInterrupt:
        print("\nApplication terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Error running application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
