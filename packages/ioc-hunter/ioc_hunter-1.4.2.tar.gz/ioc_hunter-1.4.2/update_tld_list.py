import urllib.request

with open("src/ioc_hunter/data/tld_list.txt", "wb") as f:
    tlds = urllib.request.urlopen("https://data.iana.org/TLD/tlds-alpha-by-domain.txt")
    f.writelines(tlds)