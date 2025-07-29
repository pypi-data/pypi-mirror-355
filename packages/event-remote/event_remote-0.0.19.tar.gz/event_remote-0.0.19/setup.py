import setuptools

PACKAGE_NAME = "event-remote"
package_dir = PACKAGE_NAME.replace("-", "_")

setuptools.setup(
    name=PACKAGE_NAME,  # https://pypi.org/project/event-remote/
    version='0.0.19',
    author="Circles",
    author_email="info@circlez.ai",
    description="PyPI Package for Circles event-remote Python",
    long_description="PyPI Package for Circles event-remote Python",
    long_description_content_type='text/markdown',
    url=f"https://github.com/circles-zone/{PACKAGE_NAME}-restapi-python-package",
    # packages=setuptools.find_packages(),
    packages=[package_dir],
    package_dir={package_dir: f'{package_dir}/src'},
    package_data={package_dir: ['*.py']},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'requests',
        'event-external-local>=0.0.21',
        'logger-local>=0.0.170',
        'python-sdk-remote>=0.0.93',
        'url-remote',
        'user-context-remote>=0.0.19'
    ],
)
