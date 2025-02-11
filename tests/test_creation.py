from pathlib import Path
from subprocess import run, PIPE

import pytest
import chardet

from conftest import bake_project, config_generator


def no_curlies(filepath):
    """ Utility to make sure no curly braces appear in a file.
        That is, was Jinja able to render everything?
    """
    data = filepath.open('r').read()

    template_strings = [
        '{{',
        '}}',
        '{%',
        '%}'
    ]

    template_strings_in_file = [s in data for s in template_strings]
    return not any(template_strings_in_file)


@pytest.mark.parametrize("config", config_generator())
def test_baking_configs(config):
    """ For every generated config in the config_generator, run all
        of the tests.
    """
    print("using config", config)
    with bake_project(config) as project_directory:
        verify_folders(project_directory, config)
        verify_files(project_directory, config)
        verify_makefile_commands(project_directory, config)


def verify_folders(root, config):
    ''' Tests that expected folders and only expected folders exist.
    '''
    expected_dirs = [
        '.',
        'datasets',
        'datasets/external',
        'datasets/interim',
        'datasets/final',
        'datasets/raw',
        'docs',
        'model_weights',
        'notebooks',
        'reports',
        'reports/figures',
        'logs',
        config['module_name'],
        f"{config['module_name']}/data",
        f"{config['module_name']}/features",
        f"{config['module_name']}/models",
        f"{config['module_name']}/visualization",
        f"{config['module_name']}/utils",
    ]

    expected_dirs = [
        #  (root / d).resolve().relative_to(root) for d in expected_dirs
        Path(d) for d in expected_dirs
    ]

    existing_dirs = [
        d.resolve().relative_to(root) for d in root.glob('**') if d.is_dir()
    ]

    assert sorted(existing_dirs) == sorted(expected_dirs)


def verify_files(root, config):
    ''' Test that expected files and only expected files exist.
    '''
    expected_files = [
        'Makefile',
        'README.md',
        'setup.py',
        ".env",
        ".gitignore",
        ".flake8",
        ".pre-commit-config.yaml",
        ".style.yapf",
        "datasets/external/.gitkeep",
        "datasets/interim/.gitkeep",
        "datasets/final/.gitkeep",
        "datasets/raw/.gitkeep",
        "docs/Makefile",
        "docs/commands.rst",
        "docs/conf.py",
        "docs/getting-started.rst",
        "docs/index.rst",
        "docs/make.bat",
        "notebooks/.gitkeep",
        "reports/.gitkeep",
        "reports/figures/.gitkeep",
        "model_weights/.gitkeep",
        "logs/.gitkeep",
        "test.py",
        "train.py",
        "evaluate.py",
        f"{config['module_name']}/__init__.py",
        f"{config['module_name']}/data/__init__.py",
        f"{config['module_name']}/data/make_dataset.py",
        f"{config['module_name']}/features/__init__.py",
        f"{config['module_name']}/features/build_features.py",
        f"{config['module_name']}/models/__init__.py",
        f"{config['module_name']}/models/train_model.py",
        f"{config['module_name']}/models/predict_model.py",
        f"{config['module_name']}/visualization/__init__.py",
        f"{config['module_name']}/visualization/visualize.py",
        f"{config['module_name']}/utils/__init__.py",
    ]

    # conditional files
    if not config["open_source_license"].startswith("No license"):
        expected_files.append('LICENSE')

    expected_files.append(config["dependency_file"])

    expected_files = [
        Path(f) for f in expected_files
    ]

    existing_files = [
        f.relative_to(root) for f in root.glob('**/*') if f.is_file()
    ]

    assert sorted(existing_files) == sorted(expected_files)

    for f in existing_files:
        assert no_curlies(root / f)


def verify_makefile_commands(root, config):
    """ Actually shell out to bash and run the make commands for:
        - create_environment
        - requirements
        Ensure that these use the proper environment.
    """
    test_path = Path(__file__).parent

    if config["environment_manager"] == 'conda':
        harness_path = test_path / "conda_harness.sh"
    elif config["environment_manager"] == 'virtualenv':
        harness_path = test_path / "virtualenv_harness.sh"
    elif config["environment_manager"] == 'pipenv':
        harness_path = test_path / "pipenv_harness.sh"
    elif config["environment_manager"] == 'none':
        return True
    else:
        raise ValueError(f"Environment manager '{config['environment_manager']}' not found in test harnesses.")

    result = run(["bash", str(harness_path), str(root.resolve())], stderr=PIPE, stdout=PIPE)
    result_returncode = result.returncode

    # normally hidden by pytest except in failure we want this displayed
    print("\n======================= STDOUT ======================")
    print(result.stdout.decode('utf-8'))

    print("\n======================= STDERR ======================")
    print(result.stderr.decode('utf-8'))
    assert result_returncode == 0
