from setuptools import setup, find_packages

setup(
    name="aiddit_aigc_core",
    version="0.2.32",
    author="nieqi",
    author_email="burningpush@gmail.com",
    description="aiddit aigc core package",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://www.aiddit.com",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=open('requirements.txt').read().splitlines(),
    python_requires='>=3.10',
    include_package_data=True,
)
