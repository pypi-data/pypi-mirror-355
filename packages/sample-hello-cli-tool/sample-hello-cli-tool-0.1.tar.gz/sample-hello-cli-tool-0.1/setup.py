from setuptools import setup, find_packages

setup(
    name='sample-hello-cli-tool',
    version='0.1',
    packages=find_packages(),
    install_requires=[],
    entry_points={
        "console_scripts": [
            "sample-hello-cli-tool = sample_hello_cli_tool:hello"
        ],
    },
)