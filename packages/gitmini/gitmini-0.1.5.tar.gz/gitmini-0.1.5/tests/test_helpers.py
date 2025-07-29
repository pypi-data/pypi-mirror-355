import os
import shutil
import unittest
import subprocess
import sys

# Point to project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

TEST_ENV_DIR = os.path.join(os.path.dirname(__file__), 'test_env')
GITMINI_DIR = os.path.join(TEST_ENV_DIR, '.gitmini')


class GitMiniTestCase(unittest.TestCase):
    """
    Helper classes to setup and teardown .gitmini/ repos during testing
    """

    def setUp(self):
        """ Sets up and cleans .gitmini/ each test """
        self._original_cwd = os.getcwd()
        self.repo_dir = os.path.abspath(TEST_ENV_DIR)

        # Ensure test_env exists
        if not os.path.isdir(self.repo_dir):
            os.makedirs(self.repo_dir)

        # Cleanup test_env/
        for entry in os.listdir(self.repo_dir):
            full = os.path.join(self.repo_dir, entry)
            if os.path.isdir(full):
                shutil.rmtree(full)
            else:
                os.remove(full)

        os.chdir(self.repo_dir)

        if os.path.exists(GITMINI_DIR):
            shutil.rmtree(GITMINI_DIR)

    def tearDown(self):
        # Remove .gitmini after each test
        if os.path.exists(GITMINI_DIR):
            shutil.rmtree(GITMINI_DIR)
        os.chdir(self._original_cwd)

    def run_gitmini(self, args):
        """ Runs 'gitmini' command in the test environment. """
        env = os.environ.copy()
        env['PYTHONPATH'] = self._original_cwd  # add to project PATH

        return subprocess.run(
            ['python', '-m', 'gitmini'] + args,
            cwd=self.repo_dir,
            env=env,
            capture_output=True,
            text=True
        )
