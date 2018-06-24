import json
import os
import subprocess
import unittest

from cricket.pytest.model import PyTestTestSuite


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.join(__file__)))
SAMPLE_DIR = os.path.join(ROOT_DIR, 'sample', 'pytest')


class DiscoveryTests(unittest.TestCase):
    def test_discovery(self):
        suite = PyTestTestSuite()
        runner = subprocess.run(
            suite.discover_commandline(),
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            cwd=SAMPLE_DIR,
        )

        found = set()
        for line in runner.stdout.decode('utf-8').split('\n'):
            if line:
                found.add(line)

        self.assertEqual(
            found,
            {
                'test_root.py::test_at_root',
                'tests/submodule/subsubmodule/test_deep_nesting.py::test_stuff',
                'tests/submodule/subsubmodule/test_deep_nesting.py::test_things',
                'tests/submodule/test_more_nesting.py::test_stuff',
                'tests/submodule/test_more_nesting.py::test_things',
                'tests/submodule/test_nesting.py::test_stuff',
                'tests/submodule/test_nesting.py::test_things',
                'tests/test_outcomes.py::test_assertion_item',
                'tests/test_outcomes.py::test_error_item',
                'tests/test_outcomes.py::test_failing_item',
                'tests/test_outcomes.py::test_upassed_item',
                'tests/test_outcomes.py::test_upassed_strict_item',
                'tests/test_outcomes.py::test_xfailing_item',
                'tests/test_outcomes.py::test_passing_item',
                'tests/test_outcomes.py::test_skipped_item',
                'tests/test_unusual.py::test_item_output',
                'tests/test_unusual.py::test_slow_0',
                'tests/test_unusual.py::test_slow_1',
                'tests/test_unusual.py::test_slow_2',
                'tests/test_unusual.py::test_slow_3',
                'tests/test_unusual.py::test_slow_4',
                'tests/test_unusual.py::test_slow_5',
                'tests/test_unusual.py::test_slow_6',
                'tests/test_unusual.py::test_slow_7',
                'tests/test_unusual.py::test_slow_8',
                'tests/test_unusual.py::test_slow_9',
            }
        )



class ExecutorTests(unittest.TestCase):
    def execute(self, *args):
        suite = PyTestTestSuite()
        runner = subprocess.run(
            suite.execute_commandline(list(args)),
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            cwd=SAMPLE_DIR,
        )

        found = set()
        results = {}
        for line in runner.stdout.decode('utf-8').split('\n'):
            try:
                payload = json.loads(line)
                if 'path' in payload:
                    found.add(payload['path'])
                elif 'status' in payload:
                    count = results.setdefault(payload['status'], 0)
                    results[payload['status']] = count + 1
                else:
                    self.fail("Unknown payload line: '{}'".format(payload))
            except json.JSONDecodeError:
                pass

        return found, results

    def test_run_all(self):
        found, results = self.execute()

        self.assertEqual(found, {
            'test_root.py::test_at_root',
            'tests/submodule/subsubmodule/test_deep_nesting.py::test_stuff',
            'tests/submodule/subsubmodule/test_deep_nesting.py::test_things',
            'tests/submodule/test_more_nesting.py::test_stuff',
            'tests/submodule/test_more_nesting.py::test_things',
            'tests/submodule/test_nesting.py::test_stuff',
            'tests/submodule/test_nesting.py::test_things',
            'tests/test_outcomes.py::test_assertion_item',
            'tests/test_outcomes.py::test_error_item',
            'tests/test_outcomes.py::test_failing_item',
            'tests/test_outcomes.py::test_upassed_item',
            'tests/test_outcomes.py::test_upassed_strict_item',
            'tests/test_outcomes.py::test_xfailing_item',
            'tests/test_outcomes.py::test_passing_item',
            'tests/test_outcomes.py::test_skipped_item',
            'tests/test_unusual.py::test_item_output',
            'tests/test_unusual.py::test_slow_0',
            'tests/test_unusual.py::test_slow_1',
            'tests/test_unusual.py::test_slow_2',
            'tests/test_unusual.py::test_slow_3',
            'tests/test_unusual.py::test_slow_4',
            'tests/test_unusual.py::test_slow_5',
            'tests/test_unusual.py::test_slow_6',
            'tests/test_unusual.py::test_slow_7',
            'tests/test_unusual.py::test_slow_8',
            'tests/test_unusual.py::test_slow_9',
        })

        self.assertEqual(results, {'OK': 20, 'F': 2, 'E': 1, 'x': 1, 'u': 1, 's': 1})

    def test_single_test_method(self):
        found, results = self.execute(
            'tests/submodule/test_nesting.py::test_stuff',
        )

        self.assertEqual(found, {
            'tests/submodule/test_nesting.py::test_stuff',
        })

        self.assertEqual(results, {'OK': 1})


    def test_multiple_test_methods(self):
        found, results = self.execute(
            'tests/submodule/test_nesting.py::test_stuff',
            'tests/submodule/test_nesting.py::test_things',
        )

        self.assertEqual(found, {
            'tests/submodule/test_nesting.py::test_stuff',
            'tests/submodule/test_nesting.py::test_things',
        })

        self.assertEqual(results, {'OK': 2})

    def test_module(self):
        found, results = self.execute(
            'tests/submodule/test_nesting.py',
        )

        self.assertEqual(found, {
            'tests/submodule/test_nesting.py::test_stuff',
            'tests/submodule/test_nesting.py::test_things',
        })

        self.assertEqual(results, {'OK': 2})

    def test_submodules(self):
        found, results = self.execute(
            'tests/submodule',
        )

        self.assertEqual(found, {
            'tests/submodule/subsubmodule/test_deep_nesting.py::test_stuff',
            'tests/submodule/subsubmodule/test_deep_nesting.py::test_things',
            'tests/submodule/test_more_nesting.py::test_stuff',
            'tests/submodule/test_more_nesting.py::test_things',
            'tests/submodule/test_nesting.py::test_stuff',
            'tests/submodule/test_nesting.py::test_things',
        })

        self.assertEqual(results, {'OK': 6})

    # PyTest doesn't filter test naming overlaps.
    # This is (arguably) a bug in PyTest itself.
    @unittest.expectedFailure
    def test_overlap(self):
        found, results = self.execute(
            'tests/submodule/test_nesting.py',
            'tests/submodule/test_nesting.py::test_things',
        )

        self.assertEqual(found, {
            'tests/submodule/test_nesting.py::test_stuff',
            'tests/submodule/test_nesting.py::test_things',
        })

        self.assertEqual(results, {'OK': 2})

    def test_mixed(self):
        found, results = self.execute(
            'tests/submodule/subsubmodule/test_deep_nesting.py',
            'tests/submodule/test_nesting.py::test_stuff',
        )

        self.assertEqual(found, {
            'tests/submodule/subsubmodule/test_deep_nesting.py::test_stuff',
            'tests/submodule/subsubmodule/test_deep_nesting.py::test_things',
            'tests/submodule/test_nesting.py::test_stuff',
        })

        self.assertEqual(results, {'OK': 3})
