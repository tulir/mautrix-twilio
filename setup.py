import setuptools
import glob
import mautrix_twilio

try:
    long_desc = open("README.md").read()
except IOError:
    long_desc = "Failed to read README.md"

setuptools.setup(
    name="mautrix-twilio",
    version=mautrix_twilio.__version__,
    url="https://github.com/tulir/mautrix-twilio",

    author="Tulir Asokan",
    author_email="tulir@maunium.net",

    description="A Matrix-Twilio relaybot bridge.",
    long_description=long_desc,
    long_description_content_type="text/markdown",

    packages=setuptools.find_packages(),

    install_requires=[
        "aiohttp>=3.0.1,<4",
        "mautrix>=0.4.0.dev70,<0.5.0",
        "ruamel.yaml>=0.15.94,<0.17",
        "commonmark>=0.8,<0.10",
        "python-magic>=0.4,<0.5",
        "SQLAlchemy>=1.2,<2",
        "alembic>=1,<2",
    ],
    extras_require={
        "phonenumbers": ["phonenumbers>=8,<9"],
    },

    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Topic :: Communications :: Chat",
        "Framework :: AsyncIO",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    entry_points="""
        [console_scripts]
        mautrix-twilio=mautrix_twilio.__main__:main
    """,
    data_files=[
        (".", ["example-config.yaml", "alembic.ini"]),
        ("alembic", ["alembic/env.py"]),
        ("alembic/versions", glob.glob("alembic/versions/*.py"))
    ],
)
