# CHANGELOG

## 1.4.2 - 2025-06-17

* Updated deediff and tldextract versions

## 1.4.1 - 2025-02-03

* Added support for parsing procName files


## 1.4.0 - 2025-01-31

* Added support for subdomain and root domain parsing.

## 1.3.8 - 2024-07-29

* Fixed url parsing issue in which url ends with invalid chars.

## 1.3.7 - 2024-07-22

* Fixed dynamic file types issue.

## 1.3.6 - 2024-07-22

* Supporting files with extension pst.
* Added dynamic support for new file extensions.

## 1.3.5 - 2024-07-16

* Fixed ip, domain parsing issue in stringified object.
* Fixed duplicate file names issue in file paths.

## 1.3.4 - 2024-07-08

* Supporting file name parsing with spaces in filepath.

## 1.3.3 - 2024-06-04

* Supporting ip parsing for JSON string input.

## 1.3.2 - 2024-02-20

* Added update_tld_list.py in MANIFEST.in

## 1.3.1 - 2023-10-18

* Added validation for valid IP Addresses.

## 1.3.0 - 2023-10-12

* Removed support for Python 3.6. 
* Update version for iocextract requirement.

## 1.2.0 - 2022-09-01

* Adding support for spacy ML models to be used for ioc detection.

## 1.1.2 - 2022-03-16

* Made sure iocs_to_parse is respected when pulling domains and ips from urls

## 1.1.1 - 2022-03-15

* Fix the ability to find defanged IOCs

## 1.1.0 - 2022-03-07

* Added 2 new inputs to parse_iocs: whitelist_domains, whitelist_ip_cidr_ranges
* Returned domains will now have the `www.` prefix stripped if it exists.
* improved handling of CSVs

## 1.0.0 - 2021-12-16
* Move functionality from swimbundle_utils.ioc into new repository
* Refactor code to get rid of class structure and use functions instead.
