#
# Copyright (c) 2015-2023 Thierry Florac <tflorac AT ulthar.net>
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#

"""PyAMS_*** module

"""

import os

from fanstatic import Library, Resource
from pkg_resources import Requirement, resource_filename
from zope.interface import Interface

from pyams_app_msc.skin.layer import IPyAMSMSCLayer
from pyams_layer.interfaces import IResources, ISkin
from pyams_utils.adapter import ContextRequestViewAdapter, adapter_config
from pyams_utils.registry import utility_config


__docformat__ = 'restructuredtext'

from pyams_app_msc import _


pkg_dir = resource_filename(Requirement.parse('pyams_app_msc'), 'pkg')
if not os.path.exists(pkg_dir):
    pkg_dir = '../../../pkg'  # fallback for source installation


library = Library('mscapp', pkg_dir)

msc_app = Resource(library, 'js/dev/mscapp.js',
                   minified='js/dist/mscapp.js',
                   depends=(),
                   bottom=False)


@utility_config(name='PyAMS MSC skin',
                provides=ISkin)
class PyAMSMSCSkin:
    """PyAMS MSC skin"""

    label = _("PyAMS MSC skin")
    layer = IPyAMSMSCLayer


@adapter_config(required=(Interface, IPyAMSMSCLayer, Interface),
                provides=IResources)
class PyAMSMSCSkinResources(ContextRequestViewAdapter):
    """PyAMS MSC skin resources"""

    resources = (msc_app,)
