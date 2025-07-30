from setuptools import setup, find_packages

setup(
    name="mahdi-brightness-controller",
    version="1.0.2",
    author="Muahammd Mahdi Hasan",
    author_email="mhasan3608@gmail.com",
    description="A Linux display brightness and night mode controller using tkinter",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/oxl-mahdi/mahdi-brightness-controller",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],
  entry_points={
    'console_scripts': [
        'brightness-controller = mahdi_brightness_controller.gui:main',
    ],
},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires='>=3.6',
)
