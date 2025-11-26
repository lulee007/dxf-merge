from setuptools import setup, find_packages

setup(
    name="dxf-merge",
    version="1.0.0",
    description="DXF文件合并工具",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "ezdxf",
        "numpy",
        "matplotlib",
    ],
    entry_points={
        "console_scripts": [
            "dxf-merge=dxf_processor:main",
        ],
        "gui_scripts": [
            "dxf-merge-gui=gui_app:main",
        ],
    },
)