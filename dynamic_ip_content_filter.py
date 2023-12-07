import random
import requests

class DynamicIpFilter:
    def __init__(self):
        self.trust_level_map = {}

    def SetTrustLevel(self, ip_address, trust_level):
        self.trust_level_map[ip_address] = max(-10, min(10, trust_level))

    def VerifyIpContent(self, ip_address):
        try:
            response = requests.get(ip_address)
            if response.status_code == 200:
                print(response.text)
            else:
                return False
        except requests.exceptions.RequestException:
            return False

    def FilterIp(self, ip_address):
        return
        if ip_address not in self.trust_level_map:
            self.trust_level_map[ip_address] = 0

        trust_level = self.trust_level_map[ip_address]

        if trust_level < -5:
            return False

        if trust_level >= 1 and trust_level <= 5:
            scan_chance = 1 - (0.2 * trust_level)
            if random.random() > scan_chance:
                return True

        if self.VerifyIpContent(ip_address):
            self.SetTrustLevel(ip_address, trust_level + 1)
            return True
        else:
            self.SetTrustLevel(ip_address, trust_level - 1)
            return False