from setuptools import setup, find_packages


def readme():
  with open('README.md', 'r', encoding='utf-8') as f:
    return f.read()

package_data={
        'matplobblib': ['nm/theory/htmls/*.html'],
    }

setup(
    name='matplobblib',
    version='0.2.106',
    packages=find_packages(),
    description='Just a library for some subjects',
    author='Ackrome',
    author_email='ivansergeyevicht@gmail.com',
    url='https://github.com/Ackrome/matplobblib',
    long_description=readme(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    include_package_data=True,  # Include non-Python files specified in MANIFEST.in or package_data
    package_data=package_data,
    install_requires=[
        "numpy",
        "sympy",
        "pandas",
        "scipy",
        "pyperclip",
        "pymupdf",
        "graphviz",
        "statsmodels",
        "fitz",
        "cvxopt",
        "tools",
        "beautifulsoup4"
    #    "Pillow",  # Required for image processing
    #    # Add any other dependencies here
    ],
    license='LICENSE.txt'
)
