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

import sys
import configparser

config = configparser.ConfigParser()
config.read_file(sys.stdin)

for sec in config.sections():
    print("declare -A %s" % sec)
    for key, val in config.items(sec):
        print('%s[%s]="%s"' % (sec, key, val))
