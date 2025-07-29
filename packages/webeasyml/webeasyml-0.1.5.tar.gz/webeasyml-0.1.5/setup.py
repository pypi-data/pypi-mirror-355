from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='webeasyml',
    version='0.1.5',
    description='wzai ; A simple ML web server,from wenzhou S&T High school',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='linmy',
    packages=find_packages(),
    package_data={
        'webeasyml': [
            '*.py', '*.md', '*.txt', '*.js', '*.css', '*.html'
        ],
    },
    install_requires=[
        'flask>=2.0.0,<3.0.0',
        'werkzeug>=2.0.0,<3.0.0',
        'jinja2>=3.0.0,<4.0.0',
    ],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'webeasyml=webeasyml.server:create_app',
        ],
    },
)