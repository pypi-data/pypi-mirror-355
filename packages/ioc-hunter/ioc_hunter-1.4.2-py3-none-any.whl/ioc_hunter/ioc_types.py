import re
import ipaddress
import os
import urllib

class IOCObj(object):
    def run(self, value):
        raise NotImplementedError


class AnyIOC(IOCObj):  # Always returns true
    def run(self, value):
        return True


class RegexIOC(object):
    def __init__(self, regex, re_flags=0):
        """
        :param regex: Regex String to match a value against
        """
        self.regex = re.compile(regex, re_flags)

    def run(self, value):
        return bool(self.regex.search(value))


class URLIOC(IOCObj):

    URL_REGEX_COMPILED = re.compile(r"""^                                    #beginning of line
    (?P<proto>https?:\/\/)               #protocol                http://
    (
    (?P<domain>(([\u007E-\uFFFFFF\w-]+[.])+[\u007E-\uFFFFFF\w-]{2,}))
    |
    (?P<ipv4>(?:(?:\b|\.)(?:2(?:5[0-5]|[0-4]\d)|1?\d?\d)){4})
    |
    (\[?
    (?P<ipv6>(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])))
    \]?)
    )
    (?P<port>:\d{1,5})?
    \/?                                    #domain                    www.google.co.uk
    (?P<directory>(?<=\/)([{}%|~\/!?A-Za-z0-9_.-]+)(?=\/))?                    #directory    /var/www/html/apps
    \/?                                    #final directory slash    /
    (?P<filename>([^?<>"]+))?                #filename                index.php
                                        #query marker            ?
    (?P<query>\?[^\s"<>]*)?                        #query text                cmd=login_submit&id=1#cnx=2.123
    $                                    #end of line""", re.VERBOSE | re.UNICODE)

    def run(self, value):
        match = self.URL_REGEX_COMPILED.search(value)
        if match and len(match.group()) == len(value):
            return True
        return False


COMMON_FILETYPES = ['3dm', '3ds', '3g2', '3gp', '7z', 'accdb', 'ai', 'aif', 'apk', 'app', 'asf', 'asp',
                        'aspx', 'avi', 'b', 'bak', 'bat', 'bin', 'bmp', 'c', 'cab', 'cbr', 'cer', 'cfg',
                        'cfm', 'cgi', 'class', 'cpl', 'cpp', 'crdownload', 'crx', 'cs', 'csr', 'css',
                        'csv', 'cue', 'cur', 'dat', 'db', 'dbf', 'dcr', 'dds', 'deb', 'dem', 'deskthemepack',
                        'dll', 'dmg', 'dmp', 'doc', 'docm', 'docx', 'download', 'drv', 'dtd', 'dwg', 'dxf',
                        'eps', 'exe', 'fla', 'flv', 'fnt', 'fon', 'gadget', 'gam', 'ged', 'gif', 'gpx', 'gz',
                        'h', 'hqx', 'htm', 'html', 'icns', 'ico', 'ics', 'iff', 'indd', 'ini', 'iso', 'jar',
                        'java', 'jpeg', 'jpg', 'js', 'json', 'jsp', 'key', 'keychain', 'kml', 'kmz', 'lnk',
                        'log', 'lua', 'm', 'm3u', 'm4a', 'm4v', 'max', 'mdb', 'mdf', 'mid', 'mim', 'mov',
                        'mp3', 'mp4', 'mpa', 'mpeg', 'mpg', 'msg', 'msi', 'nes', 'obj', 'odt', 'otf',
                        'pages', 'part', 'pct', 'pdb', 'pdf', 'php', 'pkg', 'pl', 'plugin', 'png', 'pps',
                        'ppt', 'pptx', 'prf', 'ps', 'psd', 'pspimage', 'py', 'rar', 'rm', 'rom', 'rpm',
                        'rss', 'rtf', 'sav', 'sdf', 'sh', 'sitx', 'sln', 'sql', 'srt', 'svg', 'swf', 'swift',
                        'sys', 'tar', 'tax2016', 'tax2017', 'tex', 'tga', 'thm', 'tif', 'tiff', 'tmp',
                        'toast', 'torrent', 'ttf', 'txt', 'uue', 'vb', 'vcd', 'vcf', 'vcxproj', 'vob', 'wav',
                        'wma', 'wmv', 'wpd', 'wps', 'wsf', 'xcodeproj', 'xhtml', 'xlr', 'xls', 'xlsx',
                        'xlsm', 'xml', 'yuv', 'zip', 'zipx', 'webm', 'flac', 'numbers', 'pst']

class FilenameIOC(IOCObj):

    FILE_REGEX = re.compile(r'^(?!.*[\\/:*"<>|])[\w !@#$%^&*()+=\[\]{}\'"-]+(\.[\w -]+)?$')

    def run(self, value):
        match = self.FILE_REGEX.search(value)
        if match and self.is_filename(match.group()):
            return True
        return False

    def is_filename(self, filename):

        extension = ".".join(filename.split(".")[-1:])

        if extension != filename and extension in COMMON_FILETYPES:
            return True
        else:
            return False


class DomainIOC(IOCObj):
    NUMERIC_NOT_A_DOMAIN = re.compile(r'^([0-9]+\.)+[0-9]+$')
    GENERAL_DOMAIN = re.compile(r'(([\u007E-\uFFFFFF\w-]+[.])+[\u007E-\uFFFFFF\w-]{2,})', re.UNICODE)
    with open(os.path.join(os.path.dirname(__file__), 'data/tld_list.txt'), 'r') as f:
        COMMON_TLDS = [line.strip() for line in f]

    def ends_with_tld(self, domain):
        for tld in self.COMMON_TLDS:
            if domain.split('.')[-1].lower() == tld.lower():
                return True
        return False

    def run(self, value, check_tld=True):
        value = urllib.parse.unquote(value)
        match = self.GENERAL_DOMAIN.search(value)
        if match and len(match.group()) == len(value):
            bad_match = self.NUMERIC_NOT_A_DOMAIN.search(value)
            if not bad_match or len(bad_match.group()) != len(value):
                if check_tld:
                    if self.ends_with_tld(value):
                        return True
                else:
                    return True

        return False


class IPIOC(IOCObj):

    REGEX = None

    def privacy_valid(self, value):
        # Return true if the value is private otherwise false if public
        ipaddr = ipaddress.ip_address(str(value))
        return ipaddr.is_private == self.is_private()

    def is_private(self):
        # Return true if the ioc typer is for private ips only else false for public
        raise NotImplementedError

    def ip_ver(self):
        # Return ip version, either 4 or 6
        raise NotImplementedError

    def run(self, value):
        match = self.REGEX.search(value)
        result = False

        try:
            ipaddress.ip_address(str(value))  # Try parsing IP
        except ValueError:
            return False

        if match:
            result = True and self.privacy_valid(value)

        return result


class IPv4PublicIOC(IPIOC):

    REGEX = re.compile(r'^(?:(?:\b|\.)(?:2(?:5[0-5]|[0-4]\d)|1?\d?\d)){4}$')

    def is_private(self):
        return False

    def ip_ver(self):
        return "4"


class IPv4PrivateIOC(IPv4PublicIOC):
    def is_private(self):
        return True


class IPv6PublicIOC(IPIOC):
    REGEX = re.compile(r'^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))$')

    def is_private(self):
        return False

    def ip_ver(self):
        return "6"


class IPv6PrivateIOC(IPv6PublicIOC):
    def is_private(self):
        return True
