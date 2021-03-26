from ipaddress import ip_address, ip_network


class IPEntity(object):
    def __init__(self, value):
        try:
            self.ip = ip_address(value)
            self.type = 'address'
        except ValueError:
            self.ip = ip_network(value)
            self.type = 'network'

    def matches(self, other):
        """Check if two IP entities match.

        Entities match if:
         - they're eqivalent ip addresses
         - self is a network, and other is an address within that network
        """
        if not isinstance(other, IPEntity):
            # This will raise a ValueError if other is not a valid ip address
            other = ip_address(other)

        if self.type == 'address':
            return self.ip == other
        else:
            return other in self.ip

    def __repr__(self):
        return f'{self.__class__.__name__} {self.type} {self.ip}'
