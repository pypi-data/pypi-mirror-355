# Copyright (C) 2014-2020 Syracuse University, European Gravitational Observatory, and Christopher Newport University.
# Written by Ryan Fisher, Gary Hemming, and Duncan Brown. See the NOTICE file distributed with this work for additional
# information regarding copyright ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import socket

from igwn_auth_utils import (
    IgwnAuthError,
    find_scitoken,
    find_x509_credentials,
    scitoken_authorization_header,
)

from urllib import request as urllib_request

SCITOKEN_READ_SCOPE = "dqsegdb.read"
SCITOKEN_WRITE_SCOPE = "dqsegdb.create"
SCITOKEN_SERVER_AUD = "https://segments.ligo.org"

#
# =============================================================================
#
#                Library for DQSEGDB API Providing URL Functions
#
# =============================================================================
#


def _auth_request(
    request,
    logger=None,
    warnings=False,
    token_audience=None,
    token_scope=SCITOKEN_READ_SCOPE,
    **kwargs,
):
    """Send a `Request` with authorization.
    """
    url = request.full_url

    if logger:
        logger.debug(f"Beginning url call: {url}")

    if request.type == "https":
        # try and find a token
        if not token_audience:
            token_audience = [
                "ANY",
                SCITOKEN_SERVER_AUD,
            ]
        try:
            token = find_scitoken(token_audience, token_scope)
        except IgwnAuthError:  # no valid token
            pass
        else:
            request.add_header(
                "Authorization",
                scitoken_authorization_header(token),
            )

        # also try and find an X.509 credential
        try:
            cert = find_x509_credentials()
        except IgwnAuthError:  # no valid X.509
            pass
        else:
            from ssl import create_default_context
            context = kwargs.setdefault("context", create_default_context())
            context.load_cert_chain(
                *(cert if isinstance(cert, tuple) else (cert,)),
            )

    # actually make the request
    with urllib_request.urlopen(request, **kwargs) as response:
        content = response.read()

    if logger:
        logger.debug("Completed URL call: %s" % url)

    # return the content
    return content


def getDataUrllib2(url, timeout=900, logger=None, **urlopen_kw):
    """Return response from server

    Parameters
    ----------
    url : `str`
        remote URL to request (HTTP or HTTPS)

    timeout : `float`
        time (seconds) to wait for reponse

    logger : `logging.Logger`
        logger to print to

    **urlopen_kw
        other keywords are passed to :func:`urllib.request.urlopen`

    Returns
    -------
    response : `str`
        the text reponse from the server
    """
    return _auth_request(
        urllib_request.Request(url),
        logger=logger,
        token_scope=SCITOKEN_READ_SCOPE,
        timeout=timeout,
        **urlopen_kw,
    )


def constructSegmentQueryURLTimeWindow(protocol, server, ifo, name, version, include_list_string, startTime, endTime):
    """
    Simple URL construction method for dqsegdb server flag:version queries
    including restrictions on time ranges.

    Parameters
    ----------
    protocol : `string`
        Ex: 'https'
    server : `string`
        Ex: 'segments.ligo.org'
    ifo : `string`
        Ex: 'L1'
    name: `string`
        Ex: 'DMT-SCIENCE'
    version : `string` or `int`
        Ex: '1'
    include_list_string : `string`
        Ex: "metadata,known,active"
    startTime : `int`
        Ex: 999999999
    endTime : `int`
        Ex: 999999999

    """
    url1 = protocol + "://" + server + "/dq"
    url2 = '/'.join([url1, ifo, name, str(version)])
    # include_list_string should be a comma-separated list expressed as a string for the URL
    # Let's pass it as a Python string for now?  Fix!!!
    start = 's=%i' % startTime
    end = 'e=%i' % endTime
    url3 = url2 + '?' + start + '&' + end + '&include=' + include_list_string
    return url3


def constructSegmentQueryURL(protocol, server, ifo, name, version, include_list_string):
    """
    Simple URL construction method for dqsegdb server flag:version queries
    not including restrictions on time ranges.

    Parameters
    ----------
    protocol : `string`
        Ex: 'https'
    server : `string`
        Ex: 'segments.ligo.org'
    ifo : `string`
        Ex: 'L1'
    name: `string`
        Ex: 'DMT-SCIENCE'
    version : `string` or `int`
        Ex: '1'
    include_list_string : `string`
        Ex: "metadata,known,active"
    """
    url1 = protocol + "://" + server + "/dq"
    url2 = '/'.join([url1, ifo, name, version])
    url3 = url2 + '?' + 'include=' + include_list_string
    return url3


def constructVersionQueryURL(protocol, server, ifo, name):
    """
    Simple URL construction method for dqsegdb server version queries.

    Parameters
    ----------
    protocol : `string`
        Ex: 'https'
    server : `string`
        Ex: 'segments.ligo.org'
    ifo : `string`
        Ex: 'L1'
    name: `string`
        Ex: 'DMT-SCIENCE'
    """
    ## Simple URL construction method:
    url1 = protocol + "://" + server + "/dq"
    url2 = '/'.join([url1, ifo, name])
    return url2


def constructFlagQueryURL(protocol, server, ifo):
    """
    Simple URL construction method for dqsegdb server flag queries.

    Parameters
    ----------
    protocol : `string`
        Ex: 'https'
    server : `string`
        Ex: 'segments.ligo.org'
    ifo : `string`
        Ex: 'L1'
    """
    ## Simple URL construction method:
    url1 = protocol + "://" + server + "/dq"
    url2 = '/'.join([url1, ifo])
    return url2


def putDataUrllib2(url, payload, timeout=900, logger=None,
                   **urlopen_kw):
    """
    Wrapper method for urllib2 that supports PUTs to a URL.

    Parameters
    ----------
    url : `string`
        Ex: 'https://segments.ligo.org/L1/DMT-SCIENCE/1'
    payload : `string`
        JSON formatted string

    """
    socket.setdefaulttimeout(timeout)

    if isinstance(payload, str):
        payload = payload.encode('utf-8')

    request = urllib_request.Request(url, data=payload)
    request.method = "PUT"
    request.add_header('Content-Type', 'JSON')

    _auth_request(
        request,
        logger=logger,
        token_scope=SCITOKEN_WRITE_SCOPE,
        timeout=timeout,
        **urlopen_kw,
    )
    return url


def patchDataUrllib2(url, payload, timeout=900, logger=None,
                     **urlopen_kw):
    """
    Wrapper method for urllib2 that supports PATCHs to a URL.

    Parameters
    ----------
    url : `string`
        Ex: 'https://segments.ligo.org/L1/DMT-SCIENCE/1'
    payload : `string`
        JSON formatted string

    """
    socket.setdefaulttimeout(timeout)

    if isinstance(payload, str):
        payload = payload.encode('utf-8')

    request = urllib_request.Request(url, data=payload)
    request.method = "PATCH"
    request.add_header('Content-Type', 'JSON')

    _auth_request(
        request,
        logger=logger,
        token_scope=SCITOKEN_WRITE_SCOPE,
        timeout=timeout,
        **urlopen_kw,
    )
    return url
