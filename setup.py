#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, Command


info_dict = dict(
)


class PrepareDebianDist(Command):
    description = "Prepares the debian dist prior to packaging."
    user_options = []

    def initialize_options(self):
        self.cwd = None

    def finalize_options(self):
        self.cwd = os.getcwd()

    def run(self):
        with open('./debian/rules', 'a') as f:
            f.write('\noverride_dh_auto_test:\n\techo "Skip dh_auto_test"')

        self._set_copyright_file()

    def _set_copyright_file(self):
        with open('./debian/copyright', 'r') as file:
            copyright_info = file.read()

        copyright_info = copyright_info.replace('{{source}}', '')
        copyright_info = copyright_info.replace('{{years}}', '2016-2017')
        copyright_info = copyright_info.replace('{{author}}', '')
        copyright_info = copyright_info.replace('{{email}}', '')

        with open('./debian/copyright', 'w') as file:
            file.write(copyright_info)


info_dict.update(cmdclass={'prepare_debian_dist': PrepareDebianDist})
setup(**info_dict)
