from setuptools import setup, find_packages

setup(
    name='discosg',
    version='0.0.1',
    author='Shaoqing Lin, Zhuang Li',
    author_email='sqlinn@whu.edu.cn',
    description='A package for discourse-level scene graph parsing and evaluation.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/ShaoqLin/DiscoSG',
    package_dir={'': "src"},
    packages=find_packages(where='src'),
    include_package_data=True,
    python_requires=">=3.10.0",
    install_requires=[
        'torch<=2.6.0',
        'transformers',
        'tqdm',
        'nltk',
        'spacy',
        'sentence-transformers',
        'pandas',
        'numpy',
        'tabulate',
        'tqdm',
        'scikit-learn',
        'peft',
        'datasets',
        'huggingface_hub'
        # Add other dependencies needed for your package
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        # Add additional classifiers as appropriate for your project
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
    ],
)
