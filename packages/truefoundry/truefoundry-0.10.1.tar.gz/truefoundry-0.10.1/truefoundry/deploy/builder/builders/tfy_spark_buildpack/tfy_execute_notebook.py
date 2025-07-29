# This script is used as the main application file for spark applications
# when the application to be run is a notebook, the actual notebook to be
# executed is passed as an argument to this script.


import argparse
import sys

import papermill as pm


def execute_notebook(notebook_path, output_path="/tmp/output.ipynb", parameters=None):
    """
    Execute a Jupyter notebook using papermill.

    Args:
        notebook_path: Path to the input notebook
        output_path: Path for the output notebook
        parameters: Dictionary of parameters to pass to the notebook

    Raises:
        Exception: If notebook execution fails
    """
    if parameters is None:
        parameters = {}

    print(f"Starting execution of notebook: {notebook_path}")
    pm.execute_notebook(
        notebook_path,
        output_path,
        parameters=parameters,
        # TODO(gw): Replace with kernel name for venv
        kernel_name="python3",
        # Log cell by cell execution output
        # TODO(gw): Output logs to a file instead, so that they aren't merged with the container's logs
        log_output=True,
        stdout_file=sys.stdout,
        stderr_file=sys.stderr,
    )
    print(f"Successfully executed notebook: {notebook_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Execute a Jupyter notebook using papermill for Spark applications"
    )
    parser.add_argument("notebook_path", help="Path to the notebook file to execute")

    args = parser.parse_args()

    # TODO(gw): Add support for passing parameters to the notebook
    try:
        execute_notebook(args.notebook_path)
    except Exception as e:
        print(f"Error executing notebook {args.notebook_path}: {e}")
        print(
            "Exiting with status code 1 to signal failure to parent process/orchestrator"
        )
        sys.exit(1)

    # TODO(gw): Publish the output notebook to blob storage from where it could be rendered
