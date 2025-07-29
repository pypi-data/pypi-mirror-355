from pathlib import Path

from setuptools import setup


this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    version="0.0.1",
    name="streamlit-template",
    description="A html component",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/streamlit-community/streamlit-template",
    project_urls={
        "Source Code": "https://github.com/streamlit-community/streamlit-template",
        "Bug Tracker": "https://github.com/streamlit-community/streamlit-template/issues",
        "Release notes": "https://github.com/streamlit-community/streamlit-template/releases",
    },
    author="Hans Then",
    author_email="hans.then@gmail.com",
    license="MIT License",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Database :: Front-Ends",
        "Topic :: Office/Business :: Financial :: Spreadsheet",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Widget Sets",
    ],
    packages=["streamlit_template"],
    include_package_data=True,
    package_data={
        "streamlit_template": ["templates/*.css"],
    },
    entry_points={
        "console_scripts": [
            "streamlit-template = streamlit_template:print_version",
        ]
    },
    python_requires=">=3.9",
    setup_requires=["setuptools_scm"],
    install_requires=[
        "streamlit > 1.38.0",
    ],
    #use_scm_version=True,
)
