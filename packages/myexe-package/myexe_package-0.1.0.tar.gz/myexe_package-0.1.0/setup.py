from setuptools import setup, find_packages

setup(
    name="myexe-package",
    version="0.1.0",
    description="一個透過 pip 安裝的單一 EXE 包",
    packages=find_packages(),
    package_data={
        # 把 scripts 下的 exe 包進 wheel
        '': ['scripts/*.exe'],
    },
    include_package_data=True,
    entry_points={
        'console_scripts': [
            # 安裝後用 `myprog` 直接呼叫
            'myprog = myexe.launcher:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: Microsoft :: Windows',
    ],
    python_requires='>=3.6',
)
