# Certbot Loopia DNS Plugin

A Certbot plugin for automatic completion of Certbot DNS challenges when your domain is managed by Loopia DNS.

## Installing

```sh
$ pip install certbot-plugin-dns-loopia
```

## Loopa API Permissions

Your Loopa API user must have access to the following methods:

-   addZoneRecord
-   getZoneRecords
-   removeZoneRecord

## Credentials

A .ini-file with your Loopia API user must be provided. Required entries in the file:

```ini
dns_loopia_username = <your-username>@loopiapi
dns_loopia_password = <your password>
```

The path to the file is provided via the `--dns-loopia-credentials` parameter to certbot.

## Disclaimer

The plugin has no affiliation to Loopia AB.
