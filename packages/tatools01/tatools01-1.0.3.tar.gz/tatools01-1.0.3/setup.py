from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tatools01",  # tên của gói thư viện
    version="1.0.3", 
    description="Thư viện hữu ích của Tuấn Anh.",
    url="https://pypi.org/project/tatools01/",
    author="Tuấn Anh - Foxconn",
    author_email="nt.anh.fai@gmail.com",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "ruamel.yaml", 
    ],  # ultralytics 8.2.84 requires numpy<2.0.0,>=1.23.0  pip install numpy==1.26.4
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_data={"tatools01": [ "Thoi_gian/*",  ]},
    # package_dir={"": "ntanh"},
    # packages=find_packages(where="ntanh"),
    Homepage="https://github.com/ntanhfai/tact",
    Issues="https://github.com/ntanhfai/tact/issues",
    entry_points={
        "console_scripts": [
            "tact=tatools01:console_main", 
        ],
    },
)
