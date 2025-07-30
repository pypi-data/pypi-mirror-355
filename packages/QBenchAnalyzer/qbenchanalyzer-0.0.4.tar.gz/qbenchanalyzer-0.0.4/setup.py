from setuptools import setup, find_namespace_packages

setup(
    name='QBenchAnalyzer',
    version='0.0.1',
    package_dir={'': 'src'},
    packages=find_namespace_packages(where='src', include='QBenchAnalyzer.*'),
    python_requires='>=3.8, <4',
    install_requires=["qiskit>=1.2.4", "matplotlib>=3.7.5"],
)
