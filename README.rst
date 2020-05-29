certbot-dns-domeneshop
======================

Domeneshop_ DNS Authenticator plugin for certbot_.

This plugin automates the process of completing a ``dns-01`` challenge by
creating, and subsequently removing, TXT records using the `Domeneshop API`_.

.. _domeneshop: https://domene.shop
.. _`Domeneshop API`: https://api.domeneshop.no/docs
.. _certbot: https://certbot.eff.org/


Named Arguments
---------------

================================================================  =====================================
``--certbot-dns-domeneshop:dns-domeneshop-credentials``           domeneshop credentials_ INI file. **(required)**
``--certbot-dns-domeneshop:dns-domeneshop-propagation-seconds``   The number of seconds to wait for DNS to propagate before asking the ACME server to verify the DNS record(Default: 120)
================================================================  =====================================

Note that the seemingly redundant ``certbot-dns-domeneshop:`` prefix is imposed by
certbot for external plugins.

Installation
------------

.. code-block:: bash
   
   pip install certbot-dns-domeneshop

Credentials
-----------

Use of this plugin requires a configuration file containing Domeneshop API
credentials.

See the `Domeneshop API`_ documentation for more information (in Norwegian).

An example ``credentials.ini`` file:

.. code-block:: ini

   certbot_dns_domeneshop:dns_domeneshop_client_token=1234567890abcdef
   certbot_dns_domeneshop:dns_domeneshop_client_secret=1234567890abcdefghijklmnopqrstuvxyz1234567890abcdefghijklmnopqrs

The path to this file can be provided interactively or using the
``--certbot-dns-domeneshop:dns-domeneshop-credentials`` command-line argument. Certbot
records the path to this file for use during renewal, but does not store the
file's contents.

**CAUTION:** You should protect these API credentials as you would the
password to your Domeneshop user account. Users who can read this file can use these
credentials to issue arbitrary API calls on your behalf. Users who can cause
Certbot to run using these credentials can complete a ``dns-01`` challenge to
acquire new certificates or revoke existing certificates for associated
domains, even if those domains aren't being managed by this server.

If applicable, we suggest that you create API credentials for domains used by your
application, in order to reduce the potential impact of lost credentials.

Certbot will emit a warning if it detects that the credentials file can be
accessed by other users on your system. The warning reads "Unsafe permissions
on credentials configuration file", followed by the path to the credentials
file. This warning will be emitted each time Certbot uses the credentials file,
including for renewal, and cannot be silenced except by addressing the issue
(e.g., by using a command like ``chmod 600`` to restrict access to the file).


Examples
--------

To acquire a single certificate for both ``example.com`` and
``www.example.com``, waiting 120 seconds for DNS propagation (the default):

.. code-block:: bash

   certbot certonly \
     --authenticator certbot-dns-domeneshop:dns-domeneshop \
     --certbot-dns-domeneshop:dns-domeneshop-credentials ~/.secrets/certbot/domeneshop.ini \
     --certbot-dns-domeneshop:dns-domeneshop-propagation-seconds 120 \
     -d example.com \
     -d www.example.com
