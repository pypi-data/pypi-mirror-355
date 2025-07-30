from setuptools import setup, find_packages

setup(
    name="wedata-automl",
    version="0.1.6",
    packages=find_packages(include=['wedata', 'wedata.*']),
    python_requires='>=3.7',
    author="maxxhe",
    install_requires=[
        "h2o_pysparkling_3.5",
        "mlflow==2.17.2",
        "scikit-learn",
        "pandas",
        "h2o",
        "numpy<2.0",
        "flaml[automl,ts_forecast,spark]",
        "optuna"
    ],
    description="AutoML wrapper with integrated MLflow logging, designed in the wedata style.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    license="Apache 2.0",
    url="",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)