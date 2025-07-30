# -*- encoding: utf-8 -*-
import os
import re
import time
import logging

__all__ = ['NmapScan']


def _get_ports(nmap_output: str):
    result = []
    patterns = r'(\d+/tcp|udp)\s+(.+)'
    for line in nmap_output.split('\n'):
        matches = re.findall(patterns, line)
        for match in matches:
            port = match[0]
            if len(port.split('/')) != 2:
                continue

            port_number = port.split('/')[0]
            protocol = port.split('/')[1]

            pattern = r"(?!closed\b)(\b\w+\b)\s+(\w+)\s*(.*)"
            submatch = re.findall(pattern, match[1])[0]

            state = submatch[0]
            service = submatch[1]

            if len(submatch) == 3:
                version = submatch[2]
            else:
                version = ''

            result.append({
                'port': port_number,
                'protocol': protocol,
                'state': state,
                'service': service,
                'version': version
            })
    return result


def _get_other_info(nmap_output: str):
    result = {}
    patterns = {
        'mac_address': r"MAC Address: (.+)",
        'device_type': r"Device type: (.+)",
        'running': r"Running: (.+)",
        'os_cpe': r"OS CPE: (.+)",
        'os_details': r"OS details: (.+)",
        'network_distance': r"Network Distance: (.+)",
        'service_info': r"Service Info: (.+)"
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, nmap_output)
        if match:
            result[key] = match.group(1)
    return result


class NmapScan:

    def __init__(self, ip: str, min_rate: int = 1000, logger: logging = logging):
        self.logger = logger

        self.ip = ip
        self.min_rate = min_rate
        self.max_rate = min_rate * 10
        self.result = {}

        self.target_state = False
        self._target_survival_detection()
        if self.target_state is False:
            self._target_survival_detection_pn()

        self.logger.info('Target {} state: {}'.format(self.ip, self.target_state))
        if self.target_state is True:
            self._target_information_collection()

    @staticmethod
    def _get_command(command: str):
        if os.name == 'nt':
            return command
        return '{} {}'.format('sudo', command)

    def _target_survival_detection(self):
        start_time = time.time()
        self.logger.info('Start nmap -P/U/E/M/A {} {}'.format(self.ip, start_time))

        commands = [
            'nmap -PU -PE -PP -PM --min-rate {} {}'.format(self.min_rate, self.ip),
            'nmap -PS -PA -PE -PP -PM --min-rate {} {}'.format(self.min_rate, self.ip),
        ]
        for command in commands:
            result = os.popen(self._get_command(command)).read()
            for line in result.split('\n'):
                if 'open' in line:
                    self.target_state = True
                    self.logger.info('End nmap -P/U/E/M/A {} {}'.format(self.ip, time.time() - start_time))
                    return True
        self.logger.info('End nmap -P/U/E/M/A {} {}'.format(self.ip, time.time() - start_time))
        return False

    def _target_survival_detection_pn(self):
        start_time = time.time()
        self.logger.info('Start nmap -Pn {} {}'.format(self.ip, start_time))
        command = 'nmap -Pn --min-rate {} {}'.format(self.min_rate, self.ip)
        result = os.popen(self._get_command(command)).read()
        for line in result.split('\n'):
            if 'open' in line:
                self.target_state = True
                self.logger.info('End nmap -Pn {} {}'.format(self.ip, time.time() - start_time))
                return True
        self.logger.info('End nmap -Pn {} {}'.format(self.ip, time.time() - start_time))
        return False

    def _target_information_collection(self):
        start_time = time.time()
        self.logger.info('Start nmap -sTV/sUV -O {} {}'.format(self.ip, start_time))

        commands = {
            'tcp': 'nmap -sTV -O --min-rate {} {}'.format(self.min_rate, self.ip),
            'udp': 'nmap -sU --min-rate {} {}'.format(self.max_rate, self.ip),
        }

        results = {}
        for protocol, command in commands.items():
            nmap_output = os.popen(self._get_command(command)).read()

            ports = _get_ports(nmap_output=nmap_output)
            other_info = _get_other_info(nmap_output=nmap_output)
            other_info['open_ports'] = ports
            results[protocol] = other_info

        self.logger.info('End nmap -sTV/sUV -O {} {}'.format(self.ip, time.time() - start_time))
        results['ip'] = self.ip
        results['duration'] = time.time() - start_time
        self.result = results
