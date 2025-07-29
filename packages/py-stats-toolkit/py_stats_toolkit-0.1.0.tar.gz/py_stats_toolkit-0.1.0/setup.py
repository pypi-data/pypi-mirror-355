from setuptools import setup, find_packages

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="py-stats-toolkit",
    version="0.1.0",
    description="Kit d'outils statistiques avancés pour l'analyse de données",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="PhoenixGuardianTools",
    author_email="phoenixguardiantools@gmail.com",
    url="https://github.com/PhoenixGuardianTools/py-stats-toolkit",
    packages=find_packages(where='.'),
    include_package_data=True,
    package_data={
        'py_stats_toolkit': [
            'data/*.json',
        ],
    },
    install_requires=[
        "pandas>=1.3.0",
        "numpy>=1.20.0",
        "matplotlib>=3.4.0",
        "scipy>=1.7.0",
        "scikit-learn>=0.24.0"
    ],
    extras_require={
        'dev': [
            'pytest>=6.0.0',
            'pytest-cov>=2.12.0',
            'black>=21.5b2',
            'flake8>=3.9.0'
        ]
    },
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Mathematics'
    ],
    keywords='statistics, data analysis, mathematical tools',
    project_urls={
        'Documentation': 'https://github.com/PhoenixGuardianTools/py-stats-toolkit/docs',
        'Source': 'https://github.com/PhoenixGuardianTools/py-stats-toolkit',
        'Tracker': 'https://github.com/PhoenixGuardianTools/py-stats-toolkit/issues',
    }
)