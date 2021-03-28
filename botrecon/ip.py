from ipaddress import ip_address, ip_network


class IPEntity(object):
    """
    Simple wrapper around the address and network objects from the ipaddress module
    """
    def __init__(self, value):
        try:
            self.ip = ip_address(value)
            self.type = 'address'
        except ValueError:
            self.ip = ip_network(value)
            self.type = 'network'

    def matches(self, other, ignore_invalid=False):
        """Check if two IP entities match.

        Entities match if:
         - they're equivalent ip addresses
         - self is a network, and other is an address within that network
        """
        if not isinstance(other, IPEntity):
            # This will raise a ValueError if other is not a valid ip address
            try:
                other = ip_address(other)
            except ValueError:
                if ignore_invalid:
                    return False
                else:
                    raise

        if self.type == 'address':
            return self.ip == other
        else:
            return other in self.ip

    def __repr__(self):
        return f'{self.__class__.__name__} {self.type} {self.ip}'
