from setuptools import find_packages, setup

setup(
    name="certbot-plugin-dns-loopia",
    version="0.1.0",
    description="A Certbot plugin for certificate renewal using Loopia DNS",
    author="Wilhelm Gren",
    author_email="wilhelmgren@outlook.com",
    url="https://github.com/aigr20/certbot-plugin-dns-loopia",
    license="MIT",
    packages=find_packages(),
    install_requires=["certbot>=4.1.1", "acme>=4.1.1"],
    py_modules=["certbot_plugin_dns_loopia", "loopia_api"],
    entry_points={
        "certbot.plugins": [
            "dns-loopia = certbot_plugin_dns_loopia:LoopiaDnsAuthenticator",
        ]
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: System Administrators",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)
