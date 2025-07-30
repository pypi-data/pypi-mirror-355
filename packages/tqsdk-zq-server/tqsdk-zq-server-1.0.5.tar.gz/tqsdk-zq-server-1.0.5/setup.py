# -*- coding: utf-8 -*-
__author__ = 'chenli'

import setuptools

try:
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel

    class bdist_wheel(_bdist_wheel):

        def finalize_options(self):
            _bdist_wheel.finalize_options(self)
            # Mark us as not a pure python package (we have platform specific lib)
            if self.plat_name != "any":
                self.root_is_pure = False

        def get_tag(self):
            # this set's us up to build generic wheels.
            python, abi, plat = _bdist_wheel.get_tag(self)
            # We don't contain any python source
            python, abi = 'py3', 'none'
            return python, abi, plat
except ImportError:
    bdist_wheel = None

setuptools.setup(
    name='tqsdk-zq-server',
    version="1.0.5",
    description='TianQin SDK - zq_server lib',
    author='TianQin',
    author_email='tianqincn@gmail.com',
    url='https://www.shinnytech.com/tqsdk',
    packages=setuptools.find_packages(),
    include_package_data=True,
    python_requires='>=3',
    cmdclass={'bdist_wheel': bdist_wheel}
)
