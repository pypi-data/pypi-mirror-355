import unittest
import os
import sys
from datetime import datetime

from pySciTools.system_run import system_run, get_func_name_and_outdir


class Testing_system_run(unittest.TestCase):

  def test_system_run(self, debug=True):
    """
    Example usage of system_run in a test case.

    Setup environment variables and run a sample bash command.
    This example runs `echo $PATH` inside a bash shell.

    Usage:
    export CUDA_VISIBLE_DEVICES=0
    export TIME_STR=0
    export PYTHONPATH=.:pySciTools
    python -c "from pySciTools.tests.test_system_run import TestingSystemRun;\
      TestingSystemRun().test_system_run(debug=False)"

    :return:
    """
    if 'CUDA_VISIBLE_DEVICES' not in os.environ:
      os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    if 'TIME_STR' not in os.environ:
      os.environ['TIME_STR'] = '0'

    # Example: Get the function name and output directory
    func_name, outdir = get_func_name_and_outdir(self, func_name=sys._getframe().f_code.co_name, file=__file__)

    if debug:
      os.environ['SCI_DEBUG'] = '1'

    os.environ['PYTHONPATH'] = '.:pySciTools:third_party'

    # Sample bash command
    cmd_str = """
            bash echo $PATH
        """

    # Run the command using the system_run utility
    start_time = datetime.now()
    system_run(cmd_str)
    end_time = datetime.now()

    elapsed_time = (end_time - start_time).total_seconds()
    print(f"The function execution time is {elapsed_time} seconds")
    print(f"The function execution time is {elapsed_time / 60.} minutes")


