#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup

setup(name='zahapa',
      description='Haproxy check agent for zabbix-server HA status',
      version='1.0.0',
      author='Johannes H. T. Johansen',
      author_email='jojangers@gmail.com',
      license='MIT',
      url='https://github.com/jojangers/zahapa',
      download_url='https://github.com/jojangers/zahapa/tarball/1.0.0',
      packages=['zahapa'],
      install_requires=['gevent==1.2.2',
                        'pyyaml>=3.11',
                        'mysql-connector>=2.2.9'],
      keywords=['Haproxy', 'Zabbix'],
      )