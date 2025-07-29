from setuptools import setup, find_packages

setup(
    name="django-notify-framework",
    version="0.0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Django>=3.2",
    ],
    author="Rahul Saini",
    author_email="rahulsaini5123@outlook.com",
    description="Easy-to-integrate Django notification library with WebSocket support for real-time updates. (under development)",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/RahulSaini3125/django_notify",
    classifiers=[
        "Framework :: Django",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    license="MIT",
)