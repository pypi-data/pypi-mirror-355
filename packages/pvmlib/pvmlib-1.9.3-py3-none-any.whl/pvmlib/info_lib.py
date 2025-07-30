class LibraryInfo:
    version_lib = 'v1.9.3'
    name = 'pvmlib'
    author = "Jesus Lizarraga"
    author_email = "jesus.lizarragav@coppel.com"
    description = "Python library for PVM"
    python_requires = '>=3.12'
    env = 'prod'
    
    install_requires = [
        "google-cloud-logging>=3.12.1",
        "pydantic-settings>=2.9.1",
        "pydantic>=2.11.4",
        "pytz>=2025.2",
        "circuitbreaker>=2.1.3",
        "tenacity>=9.1.2",
        "pybreaker>=1.3.0",
        "aiohttp>=3.11.18",
        "starlette>=0.13.0",
        "urllib3>=1.26.5,<2.0.0",
        "charset_normalizer>=2.0.0,<3.0.0",
        "motor>=3.7.0",
        "colorama>=0.4.6",
    ]