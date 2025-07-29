from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="mmcb_rs232-avt",
    version="1.0.19",
    author="Alan Taylor",
    author_email="avt@hep.ph.liv.ac.uk",
    maintainer="Alan Taylor",
    maintainer_email="avt@hep.ph.liv.ac.uk",
    description="ATLAS ITK Pixels Multi-Module Cycling Box environmental monitoring/control (RS232)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.ph.liv.ac.uk/avt/atlas-itk-pmmcb-rs232",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    python_requires=">=3.6",
    install_requires=[
        "numpy",
        "pandas",
        "matplotlib",
        "zmq",
        "pyserial==3.4.*",
        "tables",
        "yoctopuce",
    ],
    entry_points={
        "console_scripts": [
            "detect = mmcb.detect:main",
            "dmm = mmcb.dmm:main",
            "iv = mmcb.iv:main",
            "liveplot = mmcb.liveplot:main",
            "log2dat = mmcb.log2dat:main",
            "psuset = mmcb.psuset:main",
            "psustat = mmcb.psustat:main",
            "psuwatch = mmcb.psuwatch:main",
            "ult80 = mmcb.ult80:main",
        ]
    },
    # https://pypi.org/classifiers/
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Physics",
        "Environment :: Console",
        "Environment :: X11 Applications",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: POSIX :: Linux",
        "Natural Language :: English",
        "License :: OSI Approved :: European Union Public Licence 1.2 (EUPL 1.2)",
    ],
)
