import os
from setuptools import setup


def read(rel_path: str) -> str:
    here = os.path.abspath(os.path.dirname(__file__))
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    with open(os.path.join(here, rel_path), 'r', encoding='UTF-8') as fp:
        return fp.read()


long_description = read("README.rst")


setup(
    name='torch-model-hub',
    packages=['torch_model_hub', 'torch_model_hub.model'],
    description="Model hub for Pytorch.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    version='0.2.1',
    install_requires=[
        "torch>=1.0.0",
        "torch>=1.0.0,!=2.4.0; sys_platform == 'win32'",  # Windows CPU errors w/ 2.4.0 https://github.com/ultralytics/ultralytics/issues/15049
    ],
    url='https://gitee.com/summry/torch-model-hub',
    author='summy',
    author_email='fkfkfk2024@2925.com',
    keywords=['Pytorch', 'AI', 'Machine learning', 'Deep learning', 'torch'],
    package_data={
        # include json and txt files
        '': ['*.rst', '*.dtd', '*.tpl'],
    },
    include_package_data=True,
    python_requires='>=3.6',
    zip_safe=False
)

