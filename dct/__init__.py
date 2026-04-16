# ****************************************************************************#
# Copyright (c) 2022  Wandemberg Gibaut                                       #
# All rights reserved. This program and the accompanying materials            #
# are made available under the terms of the MIT License                       #
# which accompanies this distribution, and is available at                    #
# https://opensource.org/licenses/MIT                                         #
#                                                                             #
# Contributors:                                                               #
#      W. Gibaut                                                              #
#                                                                             #
# ****************************************************************************#


__version__ = '0.1.5'
__author__ = 'Wandemberg Gibaut'

from .api import (
    add_memory_to_group,
    convert,
    get_all_memory_objects,
    get_codelet_info,
    get_local_memory,
    get_memory_object,
    get_memory_objects_by_group,
    get_memory_objects_by_name,
    get_mongo_memory,
    get_node_info,
    get_redis_memory,
    get_tcp_memory,
    set_local_memory,
    set_memory_object,
    set_memory_objects_by_group,
    set_memory_objects_by_name,
    set_mongo_memory,
    set_redis_memory,
    set_tcp_memory,
)

from .mind import Mind
