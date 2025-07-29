"""
:authors: @litemat
:license: The MIT License (MIT), see LICENSE file
:copyright: (c) 2025 @litemat
"""

from dotenv import dotenv_values


class AltelConfig:
    def __init__(self, env_file='.env'):
        config = dotenv_values(env_file)
        self.username = config.get('ALTEL_USERNAME')
        self.password = config.get('ALTEL_PASSWORD')
