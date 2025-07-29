# -*- coding: utf-8 -*-
# python setup.py sdist bdist_wheel
# python -m twine upload dist/*

from __future__ import unicode_literals

import setuptools

with open("README.md", "r", encoding="utf-8", errors="ignore") as fh:
    long_description = fh.read()

setuptools.setup(
    name="PJYSDK",
    version="1.0.8",
    author="huaishan",
    author_email="admin@paojiaoyun.com",
    description=u"泡椒云网络验证 Python SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://www.paojiaoyun.com",
    project_urls={
        "Docs": "https://docs.paojiaoyun.com/py_sdk.html",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    # package_dir={"": "PJYSDK"},
    packages=["PJYSDK"],
    install_requires=['requests>=2.27'],
    python_requires=">=3.6",
)
