from setuptools import setup, find_packages

setup(
    name='vis_wizard',
    version='0.1.0',
    description='AI Data Visualization Made Easy',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Rayyan Ahmed',
    author_email='rayyannabeel22@gmail.com',
    # url='https://github.com/yourusername/vis_wizard',  # Optional but useful
    packages=find_packages(),
    install_requires=[
        'matplotlib',
        'pandas',
        'seaborn'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
    python_requires='>=3.6',
)
