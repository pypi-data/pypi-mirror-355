from setuptools import setup, find_packages

setup(
    name='swiftpredict',
    version='0.1.1',
    author='Manas Ranjan Jena',
    author_email='mranjanjena253@gmail.com',
    description='A lightweight AutoML and experiment tracking library with FastAPI backend and Python SDK',
    long_description_content_type='text/markdown',
    url='https://github.com/ManasRanjanJena253/SwiftPredict',
    packages=find_packages(where='backend/swiftpredict'),
    package_dir={'': 'backend/swiftpredict'},
    include_package_data=True,
    install_requires=[
        'fastapi',
        'uvicorn',
        'pymongo',
        'click',
        'scikit-learn',
        'matplotlib',
        'seaborn',
        'pandas',
        'numpy',
        'streamlit',
        'requests',
        'imbalanced-learn',  # correct PyPI name for imblearn
        'xgboost',
        'lightgbm',
        'scipy',
        'tqdm'
    ],
    entry_points={
        'console_scripts': [
            'swiftpredict=cli:cli',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
)
