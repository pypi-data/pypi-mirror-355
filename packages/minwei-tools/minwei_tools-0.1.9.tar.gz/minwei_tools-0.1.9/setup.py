from setuptools import setup, find_packages

setup(
    name='minwei_tools',
    version='0.1.9',
    author='OUYANGMINWEI',
    author_email='wesley91345@gmail.com',
    description='Some useful tools for Python development',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/OuYangMinOa/minwei_tools',
    packages=find_packages(),
    python_requires='>=3.9',
    entry_points = {
        'console_scripts': [
            'minwei_tools.server = minwei_tools.server:app.run',
            'minwei_tools.uv_doc = minwei_tools.uv_doc:generate_readme',
        ],
    }
)

"""
uv run python -m build
uv run twine upload dist/*
"""