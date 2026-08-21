from setuptools import setup, find_packages

setup(
    name="genai_ui_framework",
    version="0.1.0",
    packages=find_packages(include=["genai_ui_framework", "genai_ui_framework.*"]),
    include_package_data=True,
    package_data={
        "genai_ui_framework": [
            "static/*",
            "static/**/*",
        ],
    },
    install_requires=[
        "nicegui==1.4.34",
    ],
)
