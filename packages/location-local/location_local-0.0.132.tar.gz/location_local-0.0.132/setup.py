import setuptools

PACKAGE_NAME = "location-local"
package_dir = PACKAGE_NAME.replace("-", "_")

setuptools.setup(
    name=PACKAGE_NAME,
    version='0.0.132',  # https://pypi.org/project/location-local/
    author="Circles",
    author_email="info@circles.ai",
    url=f"https://github.com/circles-zone/{PACKAGE_NAME}-python-package",
    packages=[package_dir],
    package_dir={package_dir: f'{package_dir}/src'},
    package_data={package_dir: ['*.py']},
    description="Location Local PyPI Package",
    long_description="This is a package for sharing common OpenCage function used in different repositories",
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "opencage>=2.3.0",
        "phonenumbers>=8.13.35",
        "database-mysql-local>=0.0.294",
        "database-infrastructure-local>=0.0.23",
        "logger-local>=0.0.59",
        "language-remote>=0.0.13",
        "python-sdk-remote>=0.0.93",
        "user-context-remote>=0.0.4"]
)
