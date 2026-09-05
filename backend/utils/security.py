import re
import socket
import ipaddress
import urllib.parse
from typing import Tuple

# Blacklisted private / internal IPv4 networks
PRIVATE_IPV4_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),         # Current network
    ipaddress.ip_network("10.0.0.0/8"),        # Private-Use
    ipaddress.ip_network("100.64.0.0/10"),     # Carrier-grade NAT
    ipaddress.ip_network("127.0.0.0/8"),       # Loopback
    ipaddress.ip_network("169.254.0.0/16"),    # Link Local / Cloud Metadata
    ipaddress.ip_network("172.16.0.0/12"),     # Private-Use
    ipaddress.ip_network("192.0.0.0/24"),      # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),      # TEST-NET-1
    ipaddress.ip_network("192.88.99.0/24"),    # 6to4 Relay Anycast
    ipaddress.ip_network("192.168.0.0/16"),    # Private-Use
    ipaddress.ip_network("198.18.0.0/15"),     # Benchmarking
    ipaddress.ip_network("198.51.100.0/24"),   # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),    # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),       # Multicast
    ipaddress.ip_network("240.0.0.0/4"),       # Reserved for Future Use
    ipaddress.ip_network("255.255.255.255/32") # Broadcast
]

# Blacklisted private / internal IPv6 networks
PRIVATE_IPV6_NETWORKS = [
    ipaddress.ip_network("::1/128"),           # Loopback
    ipaddress.ip_network("::/128"),            # Unspecified
    ipaddress.ip_network("fc00::/7"),          # Unique Local
    ipaddress.ip_network("fe80::/10"),         # Link-Local
    ipaddress.ip_network("::ffff:0:0/96"),     # IPv4-mapped
    ipaddress.ip_network("2001:db8::/32"),     # Documentation
]

FORBIDDEN_HOSTNAMES = {
    "localhost", "localhost.localdomain", "local", "internal",
    "metadata.google.internal", "instance-data", "169.254.169.254"
}

def is_ip_private_or_reserved(ip_str: str) -> bool:
    """Checks if an IP address is in a private, loopback, or cloud-metadata range."""
    try:
        ip = ipaddress.ip_address(ip_str)
        
        # Handle IPv4-mapped IPv6 (::ffff:x.x.x.x)
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
            return is_ip_private_or_reserved(str(ip.ipv4_mapped))
            
        # Handle Well-Known NAT64 Prefix (64:ff9b::/96)
        if isinstance(ip, ipaddress.IPv6Address) and ip in ipaddress.ip_network("64:ff9b::/96"):
            embedded_ipv4 = ipaddress.IPv4Address(ip.packed[-4:])
            return is_ip_private_or_reserved(str(embedded_ipv4))
            
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_unspecified:
            return True
        
        if isinstance(ip, ipaddress.IPv4Address):
            for net in PRIVATE_IPV4_NETWORKS:
                if ip in net:
                    return True
        elif isinstance(ip, ipaddress.IPv6Address):
            for net in PRIVATE_IPV6_NETWORKS:
                if ip in net:
                    return True
        return False
    except ValueError:
        return True

def is_valid_magnet_uri(url: str) -> Tuple[bool, str]:
    """Validates whether a URI is a valid BitTorrent magnet link."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme.lower() != "magnet":
            return False, "Not a magnet link."
        
        qs = urllib.parse.parse_qs(parsed.query)
        xt_list = qs.get("xt", [])
        if not xt_list:
            return False, "Magnet link is missing exact topic (xt) parameter."
        
        has_btih = False
        for xt in xt_list:
            if xt.lower().startswith("urn:btih:"):
                info_hash = xt[9:]
                if re.fullmatch(r"[0-9a-fA-F]{40}", info_hash) or re.fullmatch(r"[2-7a-zA-Z]{32}", info_hash):
                    has_btih = True
                    break
        
        if not has_btih:
            return False, "Magnet link must contain a valid BitTorrent info hash (urn:btih:)."
            
        return True, ""
    except Exception as e:
        return False, f"Invalid magnet URI: {str(e)}"

def validate_url_security(url: str) -> Tuple[bool, str]:
    """
    Validates URL to protect against SSRF, unauthorized schemes, and internal network scans.
    Supports HTTP, HTTPS, and Magnet (BitTorrent) schemes.
    Returns (is_valid, error_message).
    """
    if not url or not isinstance(url, str):
        return False, "URL cannot be empty."
    
    url_clean = url.strip()
    if len(url_clean) > 4096:
        return False, "URL length exceeds limit."
    
    try:
        parsed = urllib.parse.urlparse(url_clean)
    except Exception:
        return False, "Malformed URL format."
    
    # Handle magnet URIs
    if parsed.scheme.lower() == "magnet":
        return is_valid_magnet_uri(url_clean)
    
    if parsed.scheme.lower() not in ("http", "https"):
        return False, f"Unsupported protocol '{parsed.scheme}'. Only HTTP, HTTPS, and Magnet are permitted."
    
    hostname = parsed.hostname
    if not hostname:
        return False, "URL must contain a valid domain or host."
    
    hostname_lower = hostname.lower()
    
    # Check forbidden hostnames
    if hostname_lower in FORBIDDEN_HOSTNAMES:
        return False, "Access to localhost, private domains, or cloud metadata is strictly prohibited."
    
    if hostname_lower.endswith(".local") or hostname_lower.endswith(".internal") or hostname_lower.endswith(".lan"):
        return False, "Access to local/internal network domains is restricted."
    
    # Check if host is direct IP
    try:
        ip_obj = ipaddress.ip_address(hostname_lower)
        if is_ip_private_or_reserved(str(ip_obj)):
            return False, "Access to private or reserved IP ranges is prohibited."
    except ValueError:
        # Host is a domain name, resolve DNS to verify all resolved IPs
        try:
            addr_info = socket.getaddrinfo(hostname, None)
            if not addr_info:
                return False, f"Could not resolve host: {hostname}"
            
            for res in addr_info:
                sockaddr = res[4]
                ip_addr = sockaddr[0]
                if is_ip_private_or_reserved(ip_addr):
                    return False, f"Host '{hostname}' resolved to a restricted internal IP address ({ip_addr})."
        except socket.gaierror:
            # Could not resolve domain, could be invalid URL
            return False, f"Host domain '{hostname}' could not be resolved."
        except Exception as e:
            return False, f"Security verification failed: {str(e)}"
    
    return True, ""

def sanitize_filename(name: str, fallback: str = "media") -> str:
    """
    Sanitizes a string to make it safe for filesystem filenames across OSes.
    Removes traversal patterns, illegal characters, and trims length.
    """
    if not name:
        return fallback
    
    # Strip dangerous characters
    cleaned = re.sub(r'[\\/*?:"<>|]', '', name)
    cleaned = re.sub(r'[\r\n\t\x00]', '', cleaned)
    # Replace whitespace sequences with single space
    cleaned = re.sub(r'\s+', ' ', cleaned).strip(' .')
    
    if not cleaned:
        cleaned = fallback
        
    # Trim to 120 chars max
    if len(cleaned) > 120:
        cleaned = cleaned[:120].rstrip(' .')
        
    return cleaned
