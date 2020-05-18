#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2002-2005 John J. Lee <jjl@pobox.com>
# Copyright 2005 Gary Poster
# Copyright 2005 Zope Corporation
# Copyright 1998-2000 Gisle Aas.

# This funciton was copied from mechanize. See
# LICENSE-mechanize for licensing details.

import mechanize
from mechanize._html import content_parser, find_declared_encoding
import mechanize._form as _form
from functools import partial

def parse_file_ex(file,
                  base_uri,
                  select_default=False,
                  request_class=mechanize.Request,
                  encoding=None,
                  backwards_compat=False,
                  add_global=True):
    raw = file.read()
    root = content_parser(raw, transport_encoding=encoding)
    form_encoding = find_declared_encoding(raw) or encoding
    forms, global_form = _form.parse_forms(
        root,
        base_uri,
        select_default=select_default,
        request_class=request_class, encoding=form_encoding)
    if not add_global:
        return list(forms)
    return [global_form] + list(forms)


parse_file = partial(parse_file_ex, add_global=False)
