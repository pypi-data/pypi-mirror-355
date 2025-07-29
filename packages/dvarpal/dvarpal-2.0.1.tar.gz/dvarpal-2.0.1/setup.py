from setuptools import setup, find_packages

setup(
    name='dvarpal',
    version='2.0.1',
    description='Automated broker login and token generator using Firefox ESR and Selenium',
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author='Amit Kumar Sharma',
    author_email='amit.official@gmail.com',
    url='https://github.com/sharmaak/dvarpal',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'PyYAML~=6.0.2',
        'requests',
        'pyotp',
        'upstox-python-sdk',
        'undetected_chromedriver',
        'selenium',
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires='>=3.8',
)
