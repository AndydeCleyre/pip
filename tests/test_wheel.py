"""Tests for wheel binary packages and .dist-info."""

import imp
import os
from pip import wheel
import textwrap
from tests.test_pip import here, reset_env, run_pip, pyversion, pyversion_nodot, write_file
from tests.path import Path

FIND_LINKS = 'file://' + os.path.join(here, 'packages')

def test_uninstallation_paths():
    class dist(object):
        def get_metadata_lines(self, record):
            return ['file.py,,',
                    'file.pyc,,',
                    'file.so,,',
                    'nopyc.py']
        location = ''

    d = dist()

    paths = list(wheel.uninstallation_paths(d))

    expected = ['file.py',
                'file.pyc',
                'file.so',
                'nopyc.py',
                'nopyc.pyc']

    assert paths == expected

    # Avoid an easy 'unique generator' bug
    paths2 = list(wheel.uninstallation_paths(d))

    assert paths2 == paths


def test_pip_wheel_success():
    """
    Test 'pip wheel' success.
    """
    env = reset_env()
    run_pip('install', 'wheel')
    run_pip('install', 'markerlib')
    result = run_pip('wheel', '--no-index', '-f', FIND_LINKS, 'simple==3.0')
    wheel_file_name = 'simple-3.0-py%s-none-any.whl' % pyversion_nodot
    wheel_file_path = env.scratch/'wheelhouse'/wheel_file_name
    assert wheel_file_path in result.files_created, (wheel_file_path, result.files_created)
    assert "Successfully built simple" in result.stdout, result.stdout


def test_pip_wheel_fail():
    """
    Test 'pip wheel' failure.
    """
    env = reset_env()
    run_pip('install', 'wheel')
    run_pip('install', 'markerlib')
    result = run_pip('wheel', '--no-index', '-f', FIND_LINKS, 'wheelbroken==0.1')
    wheel_file_name = 'wheelbroken-0.1-py%s-none-any.whl' % pyversion_nodot
    wheel_file_path = env.scratch/'wheelhouse'/wheel_file_name
    assert wheel_file_path not in result.files_created, (wheel_file_path, result.files_created)
    assert "FakeError" in result.stdout, result.stdout
    assert "Failed to build wheelbroken" in result.stdout, result.stdout


def test_pip_wheel_ignore_wheels_editables():
    """
    Test 'pip wheel' ignores editables and *.whl files in requirements
    """
    env = reset_env()
    run_pip('install', 'wheel')
    run_pip('install', 'markerlib')

    local_wheel = '%s/simple.dist-0.1-py2.py3-none-any.whl' % FIND_LINKS
    local_editable = os.path.abspath(os.path.join(here, 'packages', 'FSPkg'))
    write_file('reqs.txt', textwrap.dedent("""\
        %s
        -e %s
        simple
        """ % (local_wheel, local_editable)))
    result = run_pip('wheel', '--no-index', '-f', FIND_LINKS, '-r', env.scratch_path / 'reqs.txt')
    wheel_file_name = 'simple-3.0-py%s-none-any.whl' % pyversion_nodot
    wheel_file_path = env.scratch/'wheelhouse'/wheel_file_name
    assert wheel_file_path in result.files_created, (wheel_file_path, result.files_created)
    assert "Successfully built simple" in result.stdout, result.stdout
    assert "Failed to build" not in result.stdout, result.stdout
    assert "ignoring %s" % local_wheel in result.stdout
    assert "ignoring file://%s" % local_editable in result.stdout, result.stdout


def test_pip_wheel_unpack_only():
    """
    Test 'pip wheel' unpack only.
    """
    env = reset_env()
    result = run_pip('wheel', '--unpack-only', '--no-index', '-f', FIND_LINKS, 'simple==3.0')
    wheel_file_name = 'simple-3.0-py%s-none-any.whl' % pyversion_nodot
    wheel_file_path = env.scratch/'wheelhouse'/wheel_file_name
    assert wheel_file_path not in result.files_created, (wheel_file_path, result.files_created)
    assert env.venv/'build'/'simple'/'setup.py' in result.files_created, result.files_created

