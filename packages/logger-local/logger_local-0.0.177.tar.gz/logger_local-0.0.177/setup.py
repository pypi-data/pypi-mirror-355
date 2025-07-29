import setuptools

PACKAGE_NAME = "logger-local"
package_dir = PACKAGE_NAME.replace("-", "_")

setuptools.setup(
    name=PACKAGE_NAME,
    version='0.0.177',  # https://pypi.org/project/logger-local/
    author="Circles",
    author_email="info@circlez.ai",
    description="PyPI Package for Circles Logger Python Local",
    long_description="This is a package for sharing common Logger functions used in different repositories",
    long_description_content_type="text/markdown",
    url=f"https://github.com/circles-zone/{PACKAGE_NAME}-python-package",
    packages=[package_dir],
    package_dir={package_dir: f'{package_dir}/src'},
    package_data={package_dir: ['*.py']},
    classifiers=[
        "Programming Language :: Python :: 3",
        # https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#license
        # "License :: MIT AND (Apache-2.0 OR BSD-2-Clause)",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'mysql-connector-python>=8.5.0',
        # 'haggis',  # used to edit the log levels of logging
        'logzio-python-handler>=4.1.2',  # https://pypi.org/project/logzio-python-handler/
        'user-context-remote>=0.0.21',
        'python-sdk-remote>=0.0.75'
    ],

)
