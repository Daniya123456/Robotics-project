from setuptools import setup, find_packages

setup(
    name="er-ccapi-python",
    version="0.1.0",
    description="",
    author="Energy Robotics GmbH",
    packages=find_packages(),
    install_requires=[
        "python>=3.9",
        "requests>=2.31.0",
        "apscheduler>=3.10.4",
        "rich>=13.6.0",
        "pyyaml>=6.0.1",
        "gql[all]>=3.4.1",
        "pandas>=2.1.3",
    ],
    classifiers=[
        "Programming Language :: Python :: 3.9",
        # Add more classifiers if needed
    ],
)
