#! /use/bin/env python 
# -*- coding: utf-8 -*-

# @Author: wanping0630@126.com
# @Date: 2025-06-03 10:41:53
# @LastEditors: wanping0630@126.com
# @LastEditTime: 2025-06-13 13:34:47
# @FilePath: /GPT-Utils/setup.py
# @Description: 



from setuptools import find_packages, setup
import os.path as osp
# from gptutils.version import __version__

__url__ = 'https://code.alibaba-inc.com/VCA-LLM/GPT-Utils'


def readme():
    with open('README.md', encoding='utf-8') as f:
        content = f.read()
    return content


def parse_requirements(fname='requirements.txt', with_version=True):
    """Parse the package dependencies listed in a requirements file but strips
    specific versioning information.

    Args:
        fname (str): path to requirements file
        with_version (bool, default=False): if True include version specs

    Returns:
        List[str]: list of requirements items

    CommandLine:
        python -c "import setup; print(setup.parse_requirements())"
    """
    import re
    import sys
    from os.path import exists
    require_fpath = fname

    def parse_line(line):
        """Parse information from a line in a requirements text file."""
        if line.startswith('-r '):
            # Allow specifying requirements in other files
            target = line.split(' ')[1]
            for info in parse_require_file(target):
                yield info
        else:
            info = {'line': line}
            if line.startswith('-e '):
                info['package'] = line.split('#egg=')[1]
            else:
                # Remove versioning from the package
                pat = '(' + '|'.join(['>=', '==', '>']) + ')'
                parts = re.split(pat, line, maxsplit=1)
                parts = [p.strip() for p in parts]

                info['package'] = parts[0]
                if len(parts) > 1:
                    op, rest = parts[1:]
                    if ';' in rest:
                        # Handle platform specific dependencies
                        # http://setuptools.readthedocs.io/en/latest/setuptools.html#declaring-platform-specific-dependencies
                        version, platform_deps = map(str.strip,
                                                     rest.split(';'))
                        info['platform_deps'] = platform_deps
                    else:
                        version = rest  # NOQA
                    info['version'] = (op, version)
            yield info

    def parse_require_file(fpath):
        with open(fpath, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                line = line.strip()
                if line and not line.startswith('#'):
                    for info in parse_line(line):
                        yield info

    def gen_packages_items():
        if exists(require_fpath):
            for info in parse_require_file(require_fpath):
                parts = [info['package']]
                if with_version and 'version' in info:
                    parts.extend(info['version'])
                if not sys.version.startswith('3.4'):
                    # apparently package_deps are broken in 3.4
                    platform_deps = info.get('platform_deps')
                    if platform_deps is not None:
                        parts.append(';' + platform_deps)
                item = ''.join(parts)
                yield item

    packages = list(gen_packages_items())
    return packages


if __name__ == '__main__':
    # package_path = osp.realpath(__file__)
    # dirpath = '/'.join(package_path.split('/')[:-2])
    # print(f'dir: {dirpath}')
    # dirname = package_path.split('/')[-2]
    # print(f'dirname: {dirname}')
    __version__ = "2025.06.13"
    setup(name=f'kg_utils_v0.1.0',
          version=__version__,
          description='GPT Utils',
          long_description=readme(),
          long_description_content_type='text/markdown',
          author='VCA',
          author_email='tq.vca@list.alibaba-inc.com',
          keywords='LLM GPT Utils',
          packages=find_packages(include=('gptutils')),
          include_package_data=True,
          classifiers=[
              'Development Status :: 4 - Beta',
              'License :: OSI Approved :: Apache Software License',
              'Operating System :: OS Independent',
              'Programming Language :: Python :: 3',
              'Programming Language :: Python :: 3.10',
              'Programming Language :: Python :: 3.11',
          ],
          license='Apache License 2.0',
          install_requires=parse_requirements('requirements/base.txt'),
          zip_safe=False)
