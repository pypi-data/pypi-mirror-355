from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="pytest-test-analyzer",
    version="0.1.0",
    description="A powerful tool for analyzing pytest test files and generating detailed reports",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/deekshith-poojary98/pytest-test-analyzer",
    author="Deekshith Poojary",
    maintainer="Deekshith Poojary",
    author_email="deekshithpoojary355@gmail.com",
    license='MIT',
    packages=find_packages(),
    include_package_data=True,  # Important for including templates and static files
    python_requires=">=3.7",
    keywords="pytest testing test-analysis test-automation test-reports test-statistics",
    install_requires=[
        'jinja2>=3.1.2',  # For HTML template rendering
    ],
    entry_points={
        'console_scripts': [
            'pytest-test-analyzer=pytest_test_analyzer.cli:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Framework :: Pytest",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Development Status :: 4 - Beta",
    ],
)

