from setuptools import setup, find_packages

setup(
    name="Mensajes-albiery", #nombre del paquete
    version="6.0", #La version
    description="Un paquete para saludar y despedir", #que hace el paquete
    long_description= open('README.md').read(),
    long_description_content_type='text/markdown',
    author="Albiery de Leon", #
    author_email="albiery@gmail.com",
    url="https://www.albiery.dev", #se puede poner la pagina web
    license_files=['LICENSE'],
    packages=find_packages(), #paquetes y subpaquetes que deseamos incluir en el instalador
    scripts=[],
    test_suite='tests',
    install_requires=[paquete.strip() 
                      for paquete in open("requirements.txt").readlines()],#procesa las dependecias y requirement el cual va instlando

    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.9',
        'Topic :: Utilities'

    ]
)
