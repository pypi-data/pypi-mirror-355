from setuptools import setup, find_packages

setup(
    name="django-healthwatch",
    version="0.1.0",
    author="Moataz Fawzy",
    author_email="motazfawzy73@email.com",
    description="🩺 Advanced health check for Django with alerts and admin UI",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Moataz0000/django-healthcheck-plus",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "django>=3.2",
    ],
    classifiers=[
        "Framework :: Django",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
