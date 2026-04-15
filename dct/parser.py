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

import configparser
import sys


def emit_bash_arrays(config: configparser.ConfigParser) -> None:
    for section in config.sections():
        print("declare -A %s" % section)
        for key, value in config.items(section):
            print('%s[%s]="%s"' % (section, key, value))


def main() -> None:
    config = configparser.ConfigParser()
    config.read_file(sys.stdin)
    emit_bash_arrays(config)


if __name__ == "__main__":
    main()
