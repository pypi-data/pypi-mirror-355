import os
import sys
import subprocess
import shutil
from datetime import datetime
import shlex
import unittest


def create_outdir(outdir: str) -> str:
  """
  Creates an output directory with an optional timestamp appended to the directory name.

  If the environment variable 'TIME_STR' is set to '1', the current timestamp
  will be appended to the directory name to ensure unique output directories for each run.

  Args:
  - outdir (str): The base name for the output directory.

  Returns:
  - str: The final output directory path.
  """
  TIME_STR = bool(int(os.getenv('TIME_STR', 0)))

  # Generate a timestamp string
  time_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # format as "YYYYMMDD_HHMMSS_FFF"

  # Append timestamp if required
  outdir = outdir if not TIME_STR else f"{outdir}-{time_str}"

  # Remove the directory if it exists and recreate it
  shutil.rmtree(outdir, ignore_errors=True)
  os.makedirs(outdir)

  return outdir


def get_func_name_and_outdir(
      instance: unittest.TestCase,
      func_name: str = sys._getframe().f_code.co_name,
      file: str = __file__) -> tuple:
  """
  Extracts the test function name, output directory, and prints the command to rerun the test.

  This function assumes the class name starts with "Testing_" (e.g., "Testing_system_run")
  and that the function name starts with "test_". It creates an output directory
  under 'results/{class_name}/{func_name}'.

  Args:
  - instance (unittest.TestCase): The instance of the test class.
  - func_name (str): The name of the function to test (default is the current function name).
  - file (str): The file where the test is located (default is the current file).

  Returns:
  - tuple: Contains:
    - func_name (str): The name of the test function without the "test_" prefix.
    - outdir (str): The output directory where results will be stored.
  """
  # Get class name (assumes it starts with 'Testing_')
  class_name = instance.__class__.__name__
  assert class_name.startswith('Testing_'), f"Class name should start with 'Testing_'. Got: {class_name}"

  subdir = class_name[8:]  # remove "Testing_" prefix

  # Validate that the function name starts with 'test_'
  assert func_name.startswith('test_'), f"Function name should start with 'test_'. Got: {func_name}"
  func_name = func_name[5:]  # remove 'test_' prefix

  # Create output directory under 'results/{subdir}/{func_name}'
  outdir = f'results/{subdir}/{func_name}'
  outdir = create_outdir(outdir)

  # Print the command to rerun the test
  rel_file = os.path.relpath(os.path.realpath(file), os.path.realpath(os.path.curdir))
  module_path = rel_file[:-3].replace('/', '.')
  run_str = f"""
*************************************************************
python -c "from {module_path} import {class_name};\\
  {class_name}().test_{func_name}()"
*************************************************************
"""
  print(run_str.strip())

  return func_name, outdir


def system_run(cmd_str: str):
  """
  Executes a shell command, handling the environment and subprocess execution.

  This function supports running Python, bash, or other commands by using subprocess.

  Args:
  - cmd_str (str): The command string to run in the shell.

  Raises:
  - subprocess.CalledProcessError: If the command exits with a non-zero status.
  """
  # Split the command into a list for subprocess
  cmd = shlex.split(cmd_str)

  print('\nRunning command:\n' + ' \\\n  '.join(cmd))

  # Copy the current environment variables
  current_env = os.environ.copy()

  # Handle Python commands (use current Python interpreter)
  if cmd[0] == 'python':
    cmd[0] = sys.executable  # Ensure it's using the correct Python executable
    process = subprocess.Popen(cmd, env=current_env)

  # Handle bash commands
  elif cmd[0] == 'bash':
    process = subprocess.Popen(['/bin/bash', '-o', 'xtrace', '-c', ' '.join(cmd[1:])], env=current_env)

  # Handle all other commands
  else:
    process = subprocess.Popen(cmd, env=current_env)

  # Wait for the process to complete
  process.wait()

  # If the command returns a non-zero exit code, raise an error
  if process.returncode != 0:
    raise subprocess.CalledProcessError(returncode=process.returncode, cmd=cmd)

