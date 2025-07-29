#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Module for for a Spinner class.

          A Spinner object is displaying on console a rotating or somehow
          other animated character during its existence.

          This class was taken from https://github.com/Tagar/stuff

          Example usage:

                from fb_tools.spinner import Spinner

                with Spinner("just waiting a bit.. "):
                    time.sleep(3)

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2025 by Frank Brehm, Berlin
"""

import itertools
import logging
import sys
import threading
import time
# from collections import namedtuple

# Own modules
# from .common import to_bytes
from .xlate import XLATOR

__version__ = '2.1.0'

_ = XLATOR.gettext

LOG = logging.getLogger(__name__)

CycleList = {
    'dots': {'delay': 80, 'frames': '⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'},
    'dots2': {'delay': 80, 'frames': '⣾⣽⣻⢿⡿⣟⣯⣷'},
    'dots3': {'delay': 80, 'frames': '⠋⠙⠚⠞⠖⠦⠴⠲⠳⠓'},
    'dots4': {'delay': 80, 'frames': '⠄⠆⠇⠋⠙⠸⠰⠠⠰⠸⠙⠋⠇⠆'},
    'dots5': {'delay': 80, 'frames': '⠋⠙⠚⠒⠂⠂⠒⠲⠴⠦⠖⠒⠐⠐⠒⠓⠋'},
    'dots6': {'delay': 80, 'frames': '⠁⠉⠙⠚⠒⠂⠂⠒⠲⠴⠤⠄⠄⠤⠴⠲⠒⠂⠂⠒⠚⠙⠉⠁'},
    'dots7': {'delay': 80, 'frames': '⠈⠉⠋⠓⠒⠐⠐⠒⠖⠦⠤⠠⠠⠤⠦⠖⠒⠐⠐⠒⠓⠋⠉⠈'},
    'dots8': {'delay': 80, 'frames': '⠁⠁⠉⠙⠚⠒⠂⠂⠒⠲⠴⠤⠄⠄⠤⠠⠠⠤⠦⠖⠒⠐⠐⠒⠓⠋⠉⠈⠈'},
    'dots9': {'delay': 80, 'frames': '⢹⢺⢼⣸⣇⡧⡗⡏'},
    'dots10': {'delay': 80, 'frames': '⢄⢂⢁⡁⡈⡐⡠'},
    'dots11': {'delay': 100, 'frames': '⠁⠂⠄⡀⢀⠠⠐⠈'},
    'dots12': {
        'delay': 80,
        'frames': [
            '⢀⠀',
            '⡀⠀',
            '⠄⠀',
            '⢂⠀',
            '⡂⠀',
            '⠅⠀',
            '⢃⠀',
            '⡃⠀',
            '⠍⠀',
            '⢋⠀',
            '⡋⠀',
            '⠍⠁',
            '⢋⠁',
            '⡋⠁',
            '⠍⠉',
            '⠋⠉',
            '⠋⠉',
            '⠉⠙',
            '⠉⠙',
            '⠉⠩',
            '⠈⢙',
            '⠈⡙',
            '⢈⠩',
            '⡀⢙',
            '⠄⡙',
            '⢂⠩',
            '⡂⢘',
            '⠅⡘',
            '⢃⠨',
            '⡃⢐',
            '⠍⡐',
            '⢋⠠',
            '⡋⢀',
            '⠍⡁',
            '⢋⠁',
            '⡋⠁',
            '⠍⠉',
            '⠋⠉',
            '⠋⠉',
            '⠉⠙',
            '⠉⠙',
            '⠉⠩',
            '⠈⢙',
            '⠈⡙',
            '⠈⠩',
            '⠀⢙',
            '⠀⡙',
            '⠀⠩',
            '⠀⢘',
            '⠀⡘',
            '⠀⠨',
            '⠀⢐',
            '⠀⡐',
            '⠀⠠',
            '⠀⢀',
            '⠀⡀',
        ],
    },
    'dots8Bit': {
        'delay': 80,
        'frames': '⠀⠁⠂⠃⠄⠅⠆⠇⡀⡁⡂⡃⡄⡅⡆⡇⠈⠉⠊⠋⠌⠍⠎⠏⡈⡉⡊⡋⡌⡍⡎⡏⠐⠑⠒⠓⠔⠕⠖⠗⡐⡑⡒⡓⡔⡕⡖⡗⠘⠙⠚⠛⠜⠝⠞⠟⡘⡙'
        '⡚⡛⡜⡝⡞⡟⠠⠡⠢⠣⠤⠥⠦⠧⡠⡡⡢⡣⡤⡥⡦⡧⠨⠩⠪⠫⠬⠭⠮⠯⡨⡩⡪⡫⡬⡭⡮⡯⠰⠱⠲⠳⠴⠵⠶⠷⡰⡱⡲⡳⡴⡵⡶⡷⠸⠹⠺⠻'
        '⠼⠽⠾⠿⡸⡹⡺⡻⡼⡽⡾⡿⢀⢁⢂⢃⢄⢅⢆⢇⣀⣁⣂⣃⣄⣅⣆⣇⢈⢉⢊⢋⢌⢍⢎⢏⣈⣉⣊⣋⣌⣍⣎⣏⢐⢑⢒⢓⢔⢕⢖⢗⣐⣑⣒⣓⣔⣕'
        '⣖⣗⢘⢙⢚⢛⢜⢝⢞⢟⣘⣙⣚⣛⣜⣝⣞⣟⢠⢡⢢⢣⢤⢥⢦⢧⣠⣡⣢⣣⣤⣥⣦⣧⢨⢩⢪⢫⢬⢭⢮⢯⣨⣩⣪⣫⣬⣭⣮⣯⢰⢱⢲⢳⢴⢵⢶⢷'
        '⣰⣱⣲⣳⣴⣵⣶⣷⢸⢹⢺⢻⢼⢽⢾⢿⣸⣹⣺⣻⣼⣽⣾⣿',
    },
    'line': {'delay': 130, 'frames': ['-', '\\', '|', '/']},
    'line1': {'delay': 100, 'frames': ['-', '/', '|', '\\']},
    'line2': {'delay': 100, 'frames': '⠂-–—–-'},
    'pipe': {'delay': 100, 'frames': '┤┘┴└├┌┬┐'},
    'simpleDots': {'delay': 400, 'frames': ['.  ', '.. ', '...', '   ']},
    'simpleDotsScrolling': {'delay': 200, 'frames': ['.  ', '.. ', '...', ' ..', '  .', '   ']},
    'star': {'delay': 70, 'frames': '✶✸✹✺✹✷'},
    'star2': {'delay': 80, 'frames': '+x*'},
    'flip': {'delay': 70, 'frames': "___-``'´-___"},
    'hamburger': {'delay': 100, 'frames': '☱☲☴'},
    'growVertical': {'delay': 120, 'frames': '▁▃▄▅▆▇▆▅▄▃'},
    'growHorizontal': {'delay': 120, 'frames': '▏▎▍▌▋▊▉▊▋▌▍▎'},
    'balloon': {'delay': 140, 'frames': ' .oO@* '},
    'balloon2': {'delay': 120, 'frames': '.oO°Oo.'},
    'noise': {'delay': 100, 'frames': '▓▒░'},
    'bounce': {'delay': 120, 'frames': '⠁⠂⠄⠂'},
    'boxBounce': {'delay': 120, 'frames': '▖▘▝▗'},
    'boxBounce2': {'delay': 100, 'frames': '▌▀▐▄'},
    'triangle': {'delay': 50, 'frames': '◢◣◤◥'},
    'arc': {'delay': 100, 'frames': '◜◠◝◞◡◟'},
    'circle': {'delay': 120, 'frames': '◡⊙◠'},
    'squareCorners': {'delay': 180, 'frames': '◰◳◲◱'},
    'circleQuarters': {'delay': 120, 'frames': '◴◷◶◵'},
    'circleHalves': {'delay': 50, 'frames': '◐◓◑◒'},
    'squish': {'delay': 100, 'frames': '╫╪'},
    'toggle': {'delay': 250, 'frames': '⊶⊷'},
    'toggle2': {'delay': 80, 'frames': '▫▪'},
    'toggle3': {'delay': 120, 'frames': '□■'},
    'toggle4': {'delay': 100, 'frames': '■□▪▫'},
    'toggle5': {'delay': 100, 'frames': '▮▯'},
    'toggle7': {'delay': 80, 'frames': '⦾⦿'},
    'toggle8': {'delay': 100, 'frames': '◍◌'},
    'toggle9': {'delay': 100, 'frames': '◉◎'},
    'toggle10': {'delay': 100, 'length': 2, 'frames': '㊂㊀㊁'},
    'toggle12': {'delay': 120, 'frames': '☗☖'},
    'toggle13': {'delay': 80, 'frames': '=*-'},
    'arrow': {'delay': 100, 'frames': '←↖↑↗→↘↓↙'},
    'arrow2': {
        'delay': 80,
        'length': 2,
        'frames': ['⬆️ ', '↗️ ', '➡️ ', '↘️ ', '⬇️ ', '↙️ ', '⬅️ ', '↖️ '],
    },
    'arrow3': {
        'delay': 120,
        'frames': ['▹▹▹▹▹', '▸▹▹▹▹', '▹▸▹▹▹', '▹▹▸▹▹', '▹▹▹▸▹', '▹▹▹▹▸'],
    },
    'bouncingBar': {
        'delay': 80,
        'frames': [
            '[    ]',
            '[=   ]',
            '[==  ]',
            '[=== ]',
            '[ ===]',
            '[  ==]',
            '[   =]',
            '[    ]',
            '[   =]',
            '[  ==]',
            '[ ===]',
            '[====]',
            '[=== ]',
            '[==  ]',
            '[=   ]',
        ],
    },
    'bouncingBall': {
        'delay': 80,
        'frames': [
            '( ●    )',
            '(  ●   )',
            '(   ●  )',
            '(    ● )',
            '(     ●)',
            '(    ● )',
            '(   ●  )',
            '(  ●   )',
            '( ●    )',
            '(●     )',
        ],
    },
    'smiley': {'delay': 200, 'length': 2, 'frames': ['😄', '😝']},
    'monkey': {'delay': 300, 'length': 2, 'frames': ['🙈', '🙈', '🙉', '🙊']},
    'hearts': {'delay': 100, 'length': 2, 'frames': ['💛', '💙', '💜', '💚', '❤️ ']},
    'clock': {
        'delay': 100,
        'length': 2,
        'frames': [
            '🕛',
            '🕐',
            '🕑',
            '🕒',
            '🕓',
            '🕔',
            '🕕',
            '🕖',
            '🕗',
            '🕘',
            '🕙',
            '🕚',
        ],
    },
    'earth': {'delay': 180, 'length': 2, 'frames': ['🌍', '🌎', '🌏']},
    'material': {
        'delay': 17,
        'frames': [
            '█▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁',
            '██▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁',
            '███▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁',
            '████▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁',
            '██████▁▁▁▁▁▁▁▁▁▁▁▁▁▁',
            '██████▁▁▁▁▁▁▁▁▁▁▁▁▁▁',
            '███████▁▁▁▁▁▁▁▁▁▁▁▁▁',
            '████████▁▁▁▁▁▁▁▁▁▁▁▁',
            '█████████▁▁▁▁▁▁▁▁▁▁▁',
            '█████████▁▁▁▁▁▁▁▁▁▁▁',
            '██████████▁▁▁▁▁▁▁▁▁▁',
            '███████████▁▁▁▁▁▁▁▁▁',
            '█████████████▁▁▁▁▁▁▁',
            '██████████████▁▁▁▁▁▁',
            '██████████████▁▁▁▁▁▁',
            '▁██████████████▁▁▁▁▁',
            '▁██████████████▁▁▁▁▁',
            '▁██████████████▁▁▁▁▁',
            '▁▁██████████████▁▁▁▁',
            '▁▁▁██████████████▁▁▁',
            '▁▁▁▁█████████████▁▁▁',
            '▁▁▁▁██████████████▁▁',
            '▁▁▁▁██████████████▁▁',
            '▁▁▁▁▁██████████████▁',
            '▁▁▁▁▁██████████████▁',
            '▁▁▁▁▁██████████████▁',
            '▁▁▁▁▁▁██████████████',
            '▁▁▁▁▁▁██████████████',
            '▁▁▁▁▁▁▁█████████████',
            '▁▁▁▁▁▁▁█████████████',
            '▁▁▁▁▁▁▁▁████████████',
            '▁▁▁▁▁▁▁▁████████████',
            '▁▁▁▁▁▁▁▁▁███████████',
            '▁▁▁▁▁▁▁▁▁███████████',
            '▁▁▁▁▁▁▁▁▁▁██████████',
            '▁▁▁▁▁▁▁▁▁▁██████████',
            '▁▁▁▁▁▁▁▁▁▁▁▁████████',
            '▁▁▁▁▁▁▁▁▁▁▁▁▁███████',
            '▁▁▁▁▁▁▁▁▁▁▁▁▁▁██████',
            '▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁█████',
            '▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁█████',
            '█▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁████',
            '██▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁███',
            '██▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁███',
            '███▁▁▁▁▁▁▁▁▁▁▁▁▁▁███',
            '████▁▁▁▁▁▁▁▁▁▁▁▁▁▁██',
            '█████▁▁▁▁▁▁▁▁▁▁▁▁▁▁█',
            '█████▁▁▁▁▁▁▁▁▁▁▁▁▁▁█',
            '██████▁▁▁▁▁▁▁▁▁▁▁▁▁█',
            '████████▁▁▁▁▁▁▁▁▁▁▁▁',
            '█████████▁▁▁▁▁▁▁▁▁▁▁',
            '█████████▁▁▁▁▁▁▁▁▁▁▁',
            '█████████▁▁▁▁▁▁▁▁▁▁▁',
            '█████████▁▁▁▁▁▁▁▁▁▁▁',
            '███████████▁▁▁▁▁▁▁▁▁',
            '████████████▁▁▁▁▁▁▁▁',
            '████████████▁▁▁▁▁▁▁▁',
            '██████████████▁▁▁▁▁▁',
            '██████████████▁▁▁▁▁▁',
            '▁██████████████▁▁▁▁▁',
            '▁██████████████▁▁▁▁▁',
            '▁▁▁█████████████▁▁▁▁',
            '▁▁▁▁▁████████████▁▁▁',
            '▁▁▁▁▁████████████▁▁▁',
            '▁▁▁▁▁▁███████████▁▁▁',
            '▁▁▁▁▁▁▁▁█████████▁▁▁',
            '▁▁▁▁▁▁▁▁█████████▁▁▁',
            '▁▁▁▁▁▁▁▁▁█████████▁▁',
            '▁▁▁▁▁▁▁▁▁█████████▁▁',
            '▁▁▁▁▁▁▁▁▁▁█████████▁',
            '▁▁▁▁▁▁▁▁▁▁▁████████▁',
            '▁▁▁▁▁▁▁▁▁▁▁████████▁',
            '▁▁▁▁▁▁▁▁▁▁▁▁███████▁',
            '▁▁▁▁▁▁▁▁▁▁▁▁███████▁',
            '▁▁▁▁▁▁▁▁▁▁▁▁▁███████',
            '▁▁▁▁▁▁▁▁▁▁▁▁▁███████',
            '▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁█████',
            '▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁████',
            '▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁████',
            '▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁████',
            '▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁███',
            '▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁███',
            '▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁██',
            '▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁██',
            '▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁██',
            '▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁█',
            '▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁█',
            '▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁█',
            '▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁',
            '▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁',
            '▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁',
            '▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁',
        ],
    },
    'moon': {
        'delay': 80,
        'length': 2,
        'frames': ['🌑', '🌒', '🌓', '🌔', '🌕', '🌖', '🌗', '🌘'],
    },
    'runner': {'delay': 140, 'length': 2, 'frames': ['🚶', '🏃']},
    'pong': {
        'delay': 80,
        'frames': [
            '▐⠂       ▌',
            '▐⠈       ▌',
            '▐ ⠂      ▌',
            '▐ ⠠      ▌',
            '▐  ⡀     ▌',
            '▐  ⠠     ▌',
            '▐   ⠂    ▌',
            '▐   ⠈    ▌',
            '▐    ⠂   ▌',
            '▐    ⠠   ▌',
            '▐     ⡀  ▌',
            '▐     ⠠  ▌',
            '▐      ⠂ ▌',
            '▐      ⠈ ▌',
            '▐       ⠂▌',
            '▐       ⠠▌',
            '▐       ⡀▌',
            '▐      ⠠ ▌',
            '▐      ⠂ ▌',
            '▐     ⠈  ▌',
            '▐     ⠂  ▌',
            '▐    ⠠   ▌',
            '▐    ⡀   ▌',
            '▐   ⠠    ▌',
            '▐   ⠂    ▌',
            '▐  ⠈     ▌',
            '▐  ⠂     ▌',
            '▐ ⠠      ▌',
            '▐ ⡀      ▌',
            '▐⠠       ▌',
        ],
    },
    'shark': {
        'delay': 120,
        'frames': [
            '▐|\\____________▌',
            '▐_|\\___________▌',
            '▐__|\\__________▌',
            '▐___|\\_________▌',
            '▐____|\\________▌',
            '▐_____|\\_______▌',
            '▐______|\\______▌',
            '▐_______|\\_____▌',
            '▐________|\\____▌',
            '▐_________|\\___▌',
            '▐__________|\\__▌',
            '▐___________|\\_▌',
            '▐____________|\\▌',
            '▐____________/|▌',
            '▐___________/|_▌',
            '▐__________/|__▌',
            '▐_________/|___▌',
            '▐________/|____▌',
            '▐_______/|_____▌',
            '▐______/|______▌',
            '▐_____/|_______▌',
            '▐____/|________▌',
            '▐___/|_________▌',
            '▐__/|__________▌',
            '▐_/|___________▌',
            '▐/|____________▌',
        ],
    },
    'dqpb': {'delay': 100, 'frames': 'dqpb'},
    'weather': {
        'delay': 100,
        'length': 2,
        'frames': [
            '☀️ ',
            '☀️ ',
            '☀️ ',
            '🌤 ',
            '⛅️',
            '🌥 ',
            '☁️ ',
            '🌧 ',
            '🌨 ',
            '🌧 ',
            '🌨 ',
            '🌧 ',
            '🌨 ',
            '⛈ ',
            '🌨 ',
            '🌧 ',
            '🌨 ',
            '☁️ ',
            '🌥 ',
            '⛅️',
            '🌤 ',
            '☀️ ',
            '☀️ ',
        ],
    },
    'christmas': {'delay': 400, 'length': 2, 'frames': '🌲🎄'},
    'grenade': {
        'delay': 80,
        'length': 3,
        'frames': [
            '،  ',
            '′  ',
            ' ´ ',
            ' ‾ ',
            '  ⸌',
            '  ⸊',
            '  |',
            '  ⁎',
            '  ⁕',
            ' ෴ ',
            '  ⁓',
            '   ',
            '   ',
            '   ',
        ],
    },
    'point': {'delay': 125, 'frames': ['∙∙∙', '●∙∙', '∙●∙', '∙∙●', '∙∙∙']},
    'layer': {'delay': 150, 'frames': '-=≡'},
    'betaWave': {
        'delay': 80,
        'frames': [
            'ρββββββ',
            'βρβββββ',
            'ββρββββ',
            'βββρβββ',
            'ββββρββ',
            'βββββρβ',
            'ββββββρ',
        ],
    },
    'aesthetic': {
        'delay': 80,
        'frames': [
            '▰▱▱▱▱▱▱',
            '▰▰▱▱▱▱▱',
            '▰▰▰▱▱▱▱',
            '▰▰▰▰▱▱▱',
            '▰▰▰▰▰▱▱',
            '▰▰▰▰▰▰▱',
            '▰▰▰▰▰▰▰',
            '▰▱▱▱▱▱▱',
        ],
    },
}

# =============================================================================
class Spinner(object):
    """Displaying on console a rotating or somehow other animated character."""

    default_cycle_name = 'line1'
    default_delay = 100

    # -------------------------------------------------------------------------
    def __init__(self, message, cycle_name=None, frames=None, delay=None):
        """Initialize a Spinner object."""
        self.cycle_name = cycle_name
        if not self.cycle_name:
            self.cycle_name = self.default_cycle_name

        self.frames = None
        self.delay = self.default_delay
        self.characters = 1
        length = None

        if frames:
            self.frames = frames
        else:
            if self.cycle_name not in CycleList:
                msg = _('Spinner {!r} not found.').format(self.cycle_name)
                raise KeyError(msg)

            self.frames = CycleList[self.cycle_name]['frames']
            self.delay = CycleList[self.cycle_name]['delay']
            if 'length' in CycleList[self.cycle_name]:
                length = CycleList[self.cycle_name]['length']

        self.spinner = itertools.cycle(self.frames)

        if length:
            self.characters = length
        else:
            self.characters = len(self.frames[0])
        if delay:
            self.delay = delay

        # LOG.debug('First frame is of type {!r}.'.format(self.frames[0].__class__.__name__))
        # LOG.debug('Frames has {c} characters, delay is {d} milliseconds.'.format(
        #     c=self.characters, d=self.delay))
        # len_in_codeunits = len(self.frames[0].encode('utf-16-le')) // 2
        # LOG.debug('len_in_codeunits: {}'.format(len_in_codeunits))
        # LOG.debug('len: {}'.format(len(self.frames[0].encode('utf-8'))))
        # LOG.debug('str: {}'.format(self.frames[0]))
        # LOG.debug('bytes: {}'.format(to_bytes(self.frames[0])))

        self.busy = False
        self.spinner_visible = False
        sys.stdout.write(message)

    # -------------------------------------------------------------------------
    def write_next(self):
        """Write the next character from the cycle array on the current screen position."""
        with self._screen_lock:
            if not self.spinner_visible:
                sys.stdout.write(next(self.spinner) + ' ')
                self.spinner_visible = True
                sys.stdout.flush()

    # -------------------------------------------------------------------------
    def remove_spinner(self, cleanup=False):
        """
        Remove the last visible cycle character from screen.

        If the parameter cleanup is true, then the screen cursor will be mnoved to the next line.
        """
        with self._screen_lock:
            if self.spinner_visible:
                sys.stdout.write('\b' * (self.characters + 1))
                self.spinner_visible = False
                if cleanup:
                    sys.stdout.write(' ' * self.characters)       # overwrite spinner with blank
                    sys.stdout.write('\r')                        # move to next line
                sys.stdout.flush()

    # -------------------------------------------------------------------------
    def spinner_task(self):
        """Entry point of the Thread. It is an infinite loop."""
        delay = float(self.delay) / 1000.0

        while self.busy:
            self.write_next()
            time.sleep(delay)
            self.remove_spinner()

    # -------------------------------------------------------------------------
    def __enter__(self):
        """Execute this ction, when this object will be created for the with-block."""
        if sys.stdout.isatty():
            self._screen_lock = threading.Lock()
            self.busy = True
            self.thread = threading.Thread(target=self.spinner_task)
            self.thread.start()

    # -------------------------------------------------------------------------
    def __exit__(self, exc_type, exc_val, exc_traceback):
        """Exit action at the end of the with-block."""
        if sys.stdout.isatty():
            self.busy = False
            self.remove_spinner(cleanup=True)
        else:
            sys.stdout.write('\r')


# =============================================================================
if __name__ == '__main__':

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
