from setuptools import setup
from setuptools_cythonize import get_cmdclass

setup(
    python_requires = '>=3.10',
    name='HSwindtunnel',
    packages=['HSwindtunnel'],
    version='1.0.0',
    cmdclass=get_cmdclass(),
    license='MIT',
    description='Package to compute the airflow through the HS wind tunnel',
    author='Jacob Vestergaard',
    author_email='jacobvestergaard95@gmail.com',
    url='https://github.com/jacobv95/HSwindtunnel',
    download_url='https://github.com/jacobv95/HSwindtunnel/archive/refs/tags/v1.0.tar.gz',
    keywords=['HS wind tunnel'],
    install_requires=['pyees'],
    classifiers=[
        # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        'Development Status :: 3 - Alpha',
        # Define that your audience are developers
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        # Specify which pyhton versions that you want to support
        'Programming Language :: Python :: 3',
    ],
)
