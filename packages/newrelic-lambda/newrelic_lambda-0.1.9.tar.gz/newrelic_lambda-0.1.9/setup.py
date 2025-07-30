import setuptools

with open("README.rst", "r") as f:
    README = f.read()


setuptools.setup(
    name="newrelic-lambda",
    description="New Relic Lambda",
    long_description=README,
    long_description_content_type="text/x-rst",
    license="New Relic License",
    version="0.1.9",
    author="New Relic",
    author_email="support@newrelic.com",
    install_requires=("newrelic>=5.12.0.140",),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.9",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    include_package_data=True,
    zip_safe=False,
)
