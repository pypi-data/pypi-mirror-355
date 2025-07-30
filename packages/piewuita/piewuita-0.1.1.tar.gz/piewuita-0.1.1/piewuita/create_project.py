# piewuita/create_project.py

import os
import shutil
import subprocess

def create_project(project_name, modules):
    os.makedirs(f'{project_name}', exist_ok=True)

    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    gitignore_template = os.path.join(templates_dir, '.gitignore')
    pyproject_template = os.path.join(templates_dir, 'pyproject.toml')

    files = {
        f'{project_name}/main.py' : f"# main.py\n\ndef main():\n\tpass\n\nif __name__ == '__main__':\n    main()",
        f'{project_name}/readme.md': f'# {project_name}\n\n',
    }

    for file_path, content in files.items():
        with open(file_path, 'w') as f:
            f.write(content)

    shutil.copy(gitignore_template, f'{project_name}/.gitignore')
    shutil.copy(pyproject_template, f'{project_name}/pyproject.toml')

    venv_path = os.path.join(project_name, "venv")
    pip_executable = os.path.join(venv_path, "bin", "pip")
    #pylint_executable = os.path.join(venv_path, "bin", "pylint")

    try:
        # Create virtual environment and install modules
        subprocess.run(["python3", "-m", "venv", venv_path], check=True)
        base_modules = ["black"] # "pylint"
        modules = base_modules + modules if modules else base_modules
        subprocess.run([pip_executable, "install"] + modules, check=True)
        subprocess.run(f"{pip_executable} freeze > {project_name}/requirements.txt", shell=True, check=True)

        # Generate .pylintrc using pylint from the virtual environment
        # pylintrc_path = os.path.join(project_name, ".pylintrc")
        # with open(pylintrc_path, 'w') as pylintrc_file:
        #     subprocess.run([pylint_executable, "--generate-rcfile"], stdout=pylintrc_file, check=True)

    except subprocess.CalledProcessError as e:
        print(f"Error setting up the environment: {e}")


    subprocess.run(["git", "init", project_name], check=True)
