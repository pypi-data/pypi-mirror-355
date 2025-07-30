from setuptools import setup, find_packages

setup(
    name= 'rithmetic',
    version= '0.0.12',
    packages= find_packages(),
    install_requires= [],
    entry_points={
        "console_scripts": [
            "rith = rithmetic:welcome",
            "rith-version = rithmetic:ver",
        ],
    },
)