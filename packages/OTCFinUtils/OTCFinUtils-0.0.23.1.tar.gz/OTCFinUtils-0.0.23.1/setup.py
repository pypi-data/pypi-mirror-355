from setuptools import setup

setup(
    name="OTCFinUtils",
      version="0.0.23.1",
      description="Useful functions to interact with dataverse and sharepoint",
      packages=["OTCFinUtils"],
      author="Shomoos Aldujaily",
      author_email="saldujaily@otcfin.com",
      zip_safe=False,
      install_requires=[
            "msal",
            "python-dotenv",
            "pandas",
            "azure-identity",
            "azure-keyvault-secrets",
            "openpyxl",
      ],
)
