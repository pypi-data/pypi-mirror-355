import os
import logging
# setup logging for tests
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
import pytest
import sys

# append the root package directory to sys.path
root_repo_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
if root_repo_dir not in sys.path:
    sys.path.insert(0, root_repo_dir)

root_pkg_dir = os.path.join(root_repo_dir, 'pfun_path_helper')

from pfun_path_helper import (
    get_lib_path,
    guess_package_root,
    get_path
)


def test_guess_package_root_with_directory_path():
    package_path = guess_package_root(directory_path=root_pkg_dir)
    assert package_path == root_pkg_dir


def test_guess_package_root_with_package_name():
    package_path = guess_package_root()
    assert package_path == root_pkg_dir


def test_get_lib_path_with_package_name():
    lib_path = get_lib_path(package_name='pfun_path_helper')
    assert os.path.dirname(lib_path).endswith('pfun_path_helper')


def test_get_lib_path_with_directory_path():
    lib_path = get_lib_path(directory_path=root_repo_dir)
    assert os.path.dirname(lib_path).endswith('pfun_path_helper')


def test_get_path_with_package_name_and_filename():
    resource_path = get_path(package_name='pfun_path_helper', resource_filename='__init__.py')
    assert resource_path.endswith('pfun_path_helper/__init__.py')


def main():
    # Add any setup or teardown logic here
    import pytest
    pytest.main()


if __name__ == '__main__':
    main()