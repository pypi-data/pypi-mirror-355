# ioc-hunter

IOC Hunter finds indicators of compromise (IOC). The parse_iocs function can extract IOCs from text.  
The type_ioc function can determine the IOC type of a string that you pass in.

The IOCs that are recognized are:

- ssdeep
- sha256
- sha1
- md5
- email
- ipv4_public
- ipv4_private
- ipv6_public
- ipv6_private
- filename
- domain
- url

## Parse IOCs
The parse_iocs function parses IOCs in the list above from text. There is an option
to defang the IOCs that are passed back as well as an option to provide a whitelist regex.
This will also return IOCs labeled as ``unknown`` when text is found to be suspicious, but doesn't
match any of the IOC types.

    from ioc_hunter import parse_iocs

    text = "Your text goes here"
    whitelist = r".*internaldomain\.com.*"
    iocs = parse_iocs(text, defang=False, whitelist_regex=whitlist)

```
parse_iocs

Params:
    text – A string to parse.
    defang – If True, defang any IOCs we can (see DEFANGABLE). If False, return IOCs in their fanged state.
    whitelist_regex – Any IOC matching this regex will be ignored
    iocs_to_parse – A list of IOC types to look for (see IOC_TYPES_SEARCH_ORDER for options)
    whitelist_domains – A list or CSV of domains to exclude from results. Excludes domains and URLs that match
    whitelist_ip_cidr_ranges – A list or CSV of CIDR ranges to exclude from results. Excludes IPs and URLs that match
Returns:
    A dictionary with the ioc type as the key and a list of iocs for each value.
```
## Type IOC

The type_ioc function takes in text and determines if that text matches any of the IOC types.
If it does not match any, it will return ``unkown``.


    from ioc_hunter import type_ioc
    
    suspected_ioc = "mydomain.com"
    ioc_type = type_ioc(suspected_ioc)

```
type_ioc

Params:
    ioc – The IOC to classify.
    types_to_find – A list of types you want to look for.
Returns:
    The type of the IOC as a string, (see IOC_TYPES_SEARCH_ORDER for options)
```