# Multi-threaded Web Proxy Server

Developed by Will Convertino, Nigel Malaba, and Drew Fate-Bolognone

# Introduction

This report outlines the development of a multi-threaded HTTP/HTTPS proxy server designed for secure internet traffic handling with content filtering functionalities. The server boasts features such as an LRU cache, domain moderation, and dynamic content filtering.

# Implementation Details

HTTP Proxy: Implemented to receive and forward HTTP requests, providing a foundational understanding of proxy operations.

HTTPS Proxy: Successfully handles HTTPS connections, ensuring secure data transmission and privacy standards.

Multithreading: Enhances server performance by processing multiple client requests simultaneously, preventing blocking during communication.

Allowlist and Denylist: Filters domains using customizable allow and deny lists, promoting user control over content access.

Dynamic Content Filtering System: Evaluates web page content for inappropriate material, with a trust level system to minimize overhead.

LRU Cache: Utilizes an ordered dictionary to optimize performance, reducing load times for frequently accessed web pages.

# Future Work

_Domain Parser_

Planned introduction of a domain parser to enhance content filtering capabilities through sophisticated domain analysis and categorization.

_Improved Dynamic Content Filtering_

Consideration of self-signed certificates for more accurate and lower-overhead content filtering.

# Conclusion

The project successfully delivers a functional, efficient, and secure HTTPS proxy server with multithreading, content filtering, and caching mechanisms. Future enhancements, including a domain parser, are anticipated to further elevate its performance and utility.
