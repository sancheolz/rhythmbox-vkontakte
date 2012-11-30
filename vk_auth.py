# -*- Mode: python; coding: utf-8; tab-width: 4; indent-tabs-mode: nil; -*-
#
# Copyright © 2012 dzhioev
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import cookielib
import urllib2
import urllib

from urlparse import urlparse
from html_decode import FormParser

def auth_user(email, password, client_id, scope, opener):
    response = opener.open(
        "http://oauth.vk.com/oauth/authorize?" + \
        "redirect_uri=http://oauth.vk.com/blank.html&response_type=token&" + \
        "client_id=%s&scope=%s&display=wap" % (client_id, ",".join(scope))
        )
    doc = response.read()
    parser = FormParser()
    parser.feed(doc)
    parser.close()
    if not parser.form_parsed or parser.url is None or "pass" not in parser.params or \
      "email" not in parser.params:
          raise RuntimeError("Something wrong")
    parser.params["email"] = email
    parser.params["pass"] = password
    if parser.method.lower() == "post":
        response = opener.open(parser.url, urllib.urlencode(parser.params))
    else:
        raise NotImplementedError("Method '%s'" % parser.method)
    return response.read(), response.geturl()

def give_access(doc, opener):
    parser = FormParser()
    parser.feed(doc)
    parser.close()
    if not parser.form_parsed or parser.url is None:
          raise RuntimeError("Something wrong")
    if parser.method.lower() == "post":
        response = opener.open(parser.url, urllib.urlencode(parser.params))
    else:
        raise NotImplementedError("Method '%s'" % params.method)
    return response.geturl()

def auth(email, password, client_id, scope):
    if not isinstance(scope, list):
        scope = [scope]
    opener = urllib2.build_opener(
        urllib2.HTTPCookieProcessor(cookielib.CookieJar()),
        urllib2.HTTPRedirectHandler())
    doc, url = auth_user(email, password, client_id, scope, opener)
    if urlparse(url).path != "/blank.html":
        # Need to give access to requested scope
        url = give_access(doc, opener)
    if urlparse(url).path != "/blank.html":
        return '', ''

    def split_key_value(kv_pair):
        kv = kv_pair.split("=")
        return kv[0], kv[1]

    answer = dict(split_key_value(kv_pair) for kv_pair in urlparse(url).fragment.split("&"))
    if "access_token" not in answer or "user_id" not in answer:
        raise RuntimeError("Missing some values in answer")
    return answer["access_token"], answer["user_id"]
