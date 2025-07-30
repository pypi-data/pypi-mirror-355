# THIS FILE IS EXCLUSIVELY MAINTAINED by the project aedev.tpl_project V0.3.35
""" setup of aedev namespace package portion git_repo_manager: create and maintain local/remote git repositories of Python projects. """



# noinspection PyUnresolvedReferences
import setuptools

setup_kwargs = {
    'author': 'AndiEcker',
    'author_email': 'aecker2@gmail.com',
    'classifiers': ['Development Status :: 3 - Alpha', 'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)', 'Natural Language :: English', 'Operating System :: OS Independent', 'Programming Language :: Python', 'Programming Language :: Python :: 3', 'Programming Language :: Python :: 3.9', 'Topic :: Software Development :: Libraries :: Python Modules'],
    'description': 'aedev namespace package portion git_repo_manager: create and maintain local/remote git repositories of Python projects',
    'entry_points': {'console_scripts': ['grm = aedev.git_repo_manager.__main__:main', 'git-repo-manager = aedev.git_repo_manager.__main__:main']},
    'extras_require': {'dev': ['aedev_tpl_project', 'aedev_aedev', 'anybadge', 'coverage-badge', 'aedev_git_repo_manager', 'flake8', 'mypy', 'pylint', 'pytest', 'pytest-cov', 'pytest-django', 'typing', 'types-setuptools', 'wheel', 'twine'], 'docs': [], 'tests': ['anybadge', 'coverage-badge', 'aedev_git_repo_manager', 'flake8', 'mypy', 'pylint', 'pytest', 'pytest-cov', 'pytest-django', 'typing', 'types-setuptools', 'wheel', 'twine']},
    'install_requires': ['anybadge', 'coverage', 'coverage-badge', 'flake8', 'mypy', 'packaging', 'Pillow', 'types-Pillow', 'PyGithub', 'pylint', 'pytest', 'pytest-cov', 'python-gitlab', 'requests', 'requests-toolbelt', 'setuptools', 'ae_base', 'ae_files', 'ae_paths', 'ae_dynamicod', 'ae_literal', 'ae_updater', 'ae_core', 'ae_console', 'aedev_pythonanywhere', 'aedev_setup_project'],
    'keywords': ['configuration', 'development', 'environment', 'productivity'],
    'license': 'OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
    'long_description': '<!-- THIS FILE IS EXCLUSIVELY MAINTAINED by the project aedev.aedev V0.3.25 -->\n<!-- THIS FILE IS EXCLUSIVELY MAINTAINED by the project aedev.tpl_namespace_root V0.3.14 -->\n# git_repo_manager 0.3.100\n\n[![GitLab develop](https://img.shields.io/gitlab/pipeline/aedev-group/aedev_git_repo_manager/develop?logo=python)](\n    https://gitlab.com/aedev-group/aedev_git_repo_manager)\n[![LatestPyPIrelease](\n    https://img.shields.io/gitlab/pipeline/aedev-group/aedev_git_repo_manager/release0.3.98?logo=python)](\n    https://gitlab.com/aedev-group/aedev_git_repo_manager/-/tree/release0.3.98)\n[![PyPIVersions](https://img.shields.io/pypi/v/aedev_git_repo_manager)](\n    https://pypi.org/project/aedev-git-repo-manager/#history)\n\n>aedev namespace package portion git_repo_manager: create and maintain local/remote git repositories of Python projects.\n\n[![Coverage](https://aedev-group.gitlab.io/aedev_git_repo_manager/coverage.svg)](\n    https://aedev-group.gitlab.io/aedev_git_repo_manager/coverage/index.html)\n[![MyPyPrecision](https://aedev-group.gitlab.io/aedev_git_repo_manager/mypy.svg)](\n    https://aedev-group.gitlab.io/aedev_git_repo_manager/lineprecision.txt)\n[![PyLintScore](https://aedev-group.gitlab.io/aedev_git_repo_manager/pylint.svg)](\n    https://aedev-group.gitlab.io/aedev_git_repo_manager/pylint.log)\n\n[![PyPIImplementation](https://img.shields.io/pypi/implementation/aedev_git_repo_manager)](\n    https://gitlab.com/aedev-group/aedev_git_repo_manager/)\n[![PyPIPyVersions](https://img.shields.io/pypi/pyversions/aedev_git_repo_manager)](\n    https://gitlab.com/aedev-group/aedev_git_repo_manager/)\n[![PyPIWheel](https://img.shields.io/pypi/wheel/aedev_git_repo_manager)](\n    https://gitlab.com/aedev-group/aedev_git_repo_manager/)\n[![PyPIFormat](https://img.shields.io/pypi/format/aedev_git_repo_manager)](\n    https://pypi.org/project/aedev-git-repo-manager/)\n[![PyPILicense](https://img.shields.io/pypi/l/aedev_git_repo_manager)](\n    https://gitlab.com/aedev-group/aedev_git_repo_manager/-/blob/develop/LICENSE.md)\n[![PyPIStatus](https://img.shields.io/pypi/status/aedev_git_repo_manager)](\n    https://libraries.io/pypi/aedev-git-repo-manager)\n[![PyPIDownloads](https://img.shields.io/pypi/dm/aedev_git_repo_manager)](\n    https://pypi.org/project/aedev-git-repo-manager/#files)\n\n\n## installation\n\n\nexecute the following command to install the\naedev.git_repo_manager package\nin the currently active virtual environment:\n \n```shell script\npip install aedev-git-repo-manager\n```\n\nif you want to contribute to this portion then first fork\n[the aedev_git_repo_manager repository at GitLab](\nhttps://gitlab.com/aedev-group/aedev_git_repo_manager "aedev.git_repo_manager code repository").\nafter that pull it to your machine and finally execute the\nfollowing command in the root folder of this repository\n(aedev_git_repo_manager):\n\n```shell script\npip install -e .[dev]\n```\n\nthe last command will install this package portion, along with the tools you need\nto develop and run tests or to extend the portion documentation. to contribute only to the unit tests or to the\ndocumentation of this portion, replace the setup extras key `dev` in the above command with `tests` or `docs`\nrespectively.\n\nmore detailed explanations on how to contribute to this project\n[are available here](\nhttps://gitlab.com/aedev-group/aedev_git_repo_manager/-/blob/develop/CONTRIBUTING.rst)\n\n\n## namespace portion documentation\n\ninformation on the features and usage of this portion are available at\n[ReadTheDocs](\nhttps://aedev.readthedocs.io/en/latest/_autosummary/aedev.git_repo_manager.html\n"aedev_git_repo_manager documentation").\n',
    'long_description_content_type': 'text/markdown',
    'name': 'aedev_git_repo_manager',
    'package_data': {'': []},
    'packages': ['aedev.git_repo_manager'],
    'project_urls': {'Bug Tracker': 'https://gitlab.com/aedev-group/aedev_git_repo_manager/-/issues', 'Documentation': 'https://aedev.readthedocs.io/en/latest/_autosummary/aedev.git_repo_manager.html', 'Repository': 'https://gitlab.com/aedev-group/aedev_git_repo_manager', 'Source': 'https://aedev.readthedocs.io/en/latest/_modules/aedev/git_repo_manager.html'},
    'python_requires': '>=3.9',
    'setup_requires': ['aedev_setup_project'],
    'url': 'https://gitlab.com/aedev-group/aedev_git_repo_manager',
    'version': '0.3.100',
    'zip_safe': True,
}

if __name__ == "__main__":
    setuptools.setup(**setup_kwargs)
    pass
