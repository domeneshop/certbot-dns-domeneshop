"""DNS Authenticator for Domeneshop DNS."""
import logging
import re

import zope.interface

from domeneshop.client import Client as DomeneshopClient, DomeneshopError

from certbot import errors
from certbot import interfaces
from certbot.plugins import dns_common

logger = logging.getLogger(__name__)

HELP_URL = 'https://api.domeneshop.no/docs'


@zope.interface.implementer(interfaces.IAuthenticator)
@zope.interface.provider(interfaces.IPluginFactory)
class Authenticator(dns_common.DNSAuthenticator):
    """DNS Authenticator for Domeneshop
    This Authenticator uses the Domeneshop API to fulfill a dns-01 challenge.
    """

    description = 'Obtain certificates using a DNS TXT record (if you are using Domeneshop for DNS).'
    ttl = 60

    def __init__(self, *args, **kwargs):
        super(Authenticator, self).__init__(*args, **kwargs)
        self.credentials = None

    @classmethod
    def add_parser_arguments(cls, add):  # pylint: disable=arguments-differ
        super(Authenticator, cls).add_parser_arguments(add, default_propagation_seconds=30)
        add('credentials', help='Domeneshop credentials INI file.', default='/etc/letsencrypt/domeneshop.ini')

    def more_info(self):
        return 'This plugin configures a DNS TXT record to respond to a dns-01 challenge using ' + \
               'the Domeneshop API.'

    def _setup_credentials(self):
        self.credentials = self._configure_credentials(
            'credentials',
            'Domeneshop credentials INI file',
            {
                'client-token': 'Client token for Domeneshop API, see {0}'
                .format(HELP_URL),
                'client-secret': 'Client secret for Domeneshop API, see {0}'
                .format(HELP_URL)
            }
        )

    def _get_domeneshop_client(self):
        return DomeneshopClient(
            token=self.credentials.conf('client-token'),
            secret=self.credentials.conf('client-secret')
        )

    def _domain_id_from_guesses(self, provider_domains, domain_guesses, original_domain):
        for provider_domain in provider_domains:
            if provider_domain['domain'] in domain_guesses:
                return (provider_domain['id'], provider_domain['domain'])
        raise errors.PluginError('Failed to find domain {0} (Does your account have have access to this domain?)'.format(original_domain))

    def _perform(self, domain, validation_name, validation):  # pylint: disable=arguments-differ
        client = self._get_domeneshop_client()

        provider_domains = client.get_domains()
        domain_guesses = dns_common.base_domain_name_guesses(domain)

        # Determine the domain ID and registered domain from the provider

        domain_id, registered_domain = self._domain_id_from_guesses(provider_domains, domain_guesses, domain)

        # The Domeneshop API requires only the subdomain part of the domain:

        host = re.sub(r'{0}$'.format(registered_domain), '', validation_name)
        host = re.sub(r'\.$', '', host)

        try:
            client.create_record(domain_id, {
                "type": "TXT",
                'ttl': self.ttl,
                "host": host,
                "data": validation
            })
        except DomeneshopError as e:
            logger.error('Encountered DomeneshopError during communication with API: %s', e)
            raise errors.PluginError('Encountered DomeneshopError during communication with API: {0}'.format(e))


    def _cleanup(self, domain, validation_name, validation):  # pylint: disable=arguments-differ
        client = self._get_domeneshop_client()

        provider_domains = client.get_domains()
        domain_guesses = dns_common.base_domain_name_guesses(domain)

        # Determine the domain ID and registered domain from the provider

        try:
            domain_id, registered_domain = self._domain_id_from_guesses(provider_domains, domain_guesses, domain)
        except errors.PluginError as e:
            logger.warning("Error occurred while determining domain ID for deletion: %s", e)
            return

        # The Domeneshop API requires the subdomain part of the domain:

        host = re.sub(r'{0}$'.format(registered_domain), '', validation_name)
        host = re.sub(r'\.$', '', host)

        find_record = {
            'type': 'TXT',
            'host': host,
            'data': validation
        }

        provider_records = client.get_records(domain_id)

        for record in provider_records:
            if record.items() >= find_record.items():
                try:
                    client.delete_record(domain_id, record['id'])
                except DomeneshopError as e:
                    logger.warning("Error occurred while deleting DNS record: %s", e)
