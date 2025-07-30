from setuptools import setup, find_packages

setup(
    name="urlive",
    version="0.1",
    description="A hacker-style URL status checker by GTSivam",
    author="Thirumurugan (GTSivam)",
    author_email="your-email@example.com",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.1",
        "pandas>=1.3.0"
    ],
    python_requires=">=3.8, <4.0",
)
