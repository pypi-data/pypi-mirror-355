from setuptools import setup, find_packages

setup(
    name='rocketcontent',
    version='1.0.24',
    packages=find_packages(),
    install_requires=[
        'requests',
        'PyYAML',
        'rich',
        'markdown2'        
    ],
    author='Guillermo Avendano',
    author_email='gavendano@rocketsoftware.com',
    description='Content Services Api 12.4.x',
    long_description=open('README.md', encoding='utf-8').read(),  # Especifica la codificación
    long_description_content_type='text/markdown',
    url='https://docs.rocketsoftware.com/bundle/mobiusdev_123/page/rtb1690483435152.html',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',  # Especifica la versión mínima de Python
)