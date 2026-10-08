# -*- coding: utf-8 -*-
import math

__all__ = ('color_tables', 'getRatingColors', 'getColor', 'getStatisticColor',
           'getRatingPaletteColor', 'getComparisonColor', 'getMoeDamageColor')


class ColorRating:
    def __init__(self, scale_name, colors):
        self.scale_name = scale_name
        self.colors = colors

    def table(self):
        return {
            'ScaleColor': self.scale_name,
            'colors': self.colors
        }

noob_meter_definitions = {
    'al': '#22CC00',
    'sq': '#FFB964',
    'tk': '#00EAFF',
    'en': '#F50800',
    'pl': '#FFFF2A',
    'colorRating': {
        'nocolor': '#CCCCCC',
        'very_bad': '#BB0000',
        'bad': '#FF0000',
        'b_average': '#FF6600',
        'average': '#F8F400',
        'normal': '#F8F400',
        'good': '#99CC00',
        'very_good': '#00CC00',
        'great': '#66BBFF',
        'unique': '#CC66CC',
        's_unique': '#FF00FF'
    },
    'colorHP': {
        'very_low': '#FF0000',
        'low': '#DD4444',
        'average': '#FFCC22',
        'above_average': '#EFEFEF'
    }
}

noob_meter_colors = {
    'colorRating': noob_meter_definitions['colorRating'],
    'colorHP': noob_meter_definitions['colorHP'],
    'system': {
        'ally_alive': noob_meter_definitions['al'],
        'ally_dead': '#B8FFC1',
        'ally_blowedup': '#007700',
        'squadman_alive': noob_meter_definitions['sq'],
        'squadman_dead': '#CA7000',
        'squadman_blowedup': '#A45A00',
        'teamKiller_alive': noob_meter_definitions['tk'],
        'teamKiller_dead': '#097783',
        'teamKiller_blowedup': '#096A75',
        'enemy_alive': noob_meter_definitions['en'],
        'enemy_dead': '#E29188',
        'enemy_blowedup': '#5A0401',
        'ally_base': noob_meter_definitions['al'],
        'enemy_base': noob_meter_definitions['en']
    },
    'dmg_kind': {
        'attack': '#FFAA55',
        'fire': '#FF6655',
        'ramming': '#00CCCC',
        'world_collision': '#998855',
        'other': '#CCCCCC'
    },
    'vtype': {
        'LT': '#53B329',
        'MT': '#1EA2D2',
        'HT': '#957D5B',
        'SPG': '#B87AB2',
        'TD': '#F13439',
        'premium': '#FFA804',
        'usePremiumColor': False
    },
    'spotted': {
        'neverSeen': '#000000',
        'lost': '#FF552A',
        'spotted': '#FFBB00',
        'dead': '#FFFFFF',
        'neverSeen_arty': '#000000',
        'lost_arty': '#D9D9D9',
        'spotted_arty': '#FFBB00',
        'dead_arty': '#FFFFFF'
    },
    'totalHP': {
        'bad': '#FF0000',
        'neutral': '#FFFFFF',
        'good': '#00FF00'
    },
    'damage': {
        'ally_ally_hit': noob_meter_definitions['tk'],
        'ally_ally_kill': noob_meter_definitions['tk'],
        'ally_ally_blowup': noob_meter_definitions['tk'],
        'ally_squadman_hit': noob_meter_definitions['tk'],
        'ally_squadman_kill': noob_meter_definitions['tk'],
        'ally_squadman_blowup': noob_meter_definitions['tk'],
        'ally_enemy_hit': noob_meter_definitions['en'],
        'ally_enemy_kill': noob_meter_definitions['en'],
        'ally_enemy_blowup': noob_meter_definitions['en'],
        'ally_allytk_hit': noob_meter_definitions['tk'],
        'ally_allytk_kill': noob_meter_definitions['tk'],
        'ally_allytk_blowup': noob_meter_definitions['tk'],
        'ally_enemytk_hit': noob_meter_definitions['en'],
        'ally_enemytk_kill': noob_meter_definitions['en'],
        'ally_enemytk_blowup': noob_meter_definitions['en'],
        'enemy_ally_hit': noob_meter_definitions['al'],
        'enemy_ally_kill': noob_meter_definitions['al'],
        'enemy_ally_blowup': noob_meter_definitions['al'],
        'enemy_squadman_hit': noob_meter_definitions['al'],
        'enemy_squadman_kill': noob_meter_definitions['al'],
        'enemy_squadman_blowup': noob_meter_definitions['al'],
        'enemy_enemy_hit': noob_meter_definitions['en'],
        'enemy_enemy_kill': noob_meter_definitions['en'],
        'enemy_enemy_blowup': noob_meter_definitions['en'],
        'enemy_allytk_hit': noob_meter_definitions['al'],
        'enemy_allytk_kill': noob_meter_definitions['al'],
        'enemy_allytk_blowup': noob_meter_definitions['al'],
        'enemy_enemytk_hit': noob_meter_definitions['en'],
        'enemy_enemytk_kill': noob_meter_definitions['en'],
        'enemy_enemytk_blowup': noob_meter_definitions['en'],
        'unknown_ally_hit': noob_meter_definitions['al'],
        'unknown_ally_kill': noob_meter_definitions['al'],
        'unknown_ally_blowup': noob_meter_definitions['al'],
        'unknown_squadman_hit': noob_meter_definitions['al'],
        'unknown_squadman_kill': noob_meter_definitions['al'],
        'unknown_squadman_blowup': noob_meter_definitions['al'],
        'unknown_enemy_hit': noob_meter_definitions['en'],
        'unknown_enemy_kill': noob_meter_definitions['en'],
        'unknown_enemy_blowup': noob_meter_definitions['en'],
        'unknown_allytk_hit': noob_meter_definitions['al'],
        'unknown_allytk_kill': noob_meter_definitions['al'],
        'unknown_allytk_blowup': noob_meter_definitions['al'],
        'unknown_enemytk_hit': noob_meter_definitions['en'],
        'unknown_enemytk_kill': noob_meter_definitions['en'],
        'unknown_enemytk_blowup': noob_meter_definitions['en'],
        'squadman_ally_hit': noob_meter_definitions['sq'],
        'squadman_ally_kill': noob_meter_definitions['sq'],
        'squadman_ally_blowup': noob_meter_definitions['sq'],
        'squadman_squadman_hit': noob_meter_definitions['sq'],
        'squadman_squadman_kill': noob_meter_definitions['sq'],
        'squadman_squadman_blowup': noob_meter_definitions['sq'],
        'squadman_enemy_hit': noob_meter_definitions['sq'],
        'squadman_enemy_kill': noob_meter_definitions['sq'],
        'squadman_enemy_blowup': noob_meter_definitions['sq'],
        'squadman_allytk_hit': noob_meter_definitions['sq'],
        'squadman_allytk_kill': noob_meter_definitions['sq'],
        'squadman_allytk_blowup': noob_meter_definitions['sq'],
        'squadman_enemytk_hit': noob_meter_definitions['sq'],
        'squadman_enemytk_kill': noob_meter_definitions['sq'],
        'squadman_enemytk_blowup': noob_meter_definitions['sq'],
        'player_ally_hit': noob_meter_definitions['pl'],
        'player_ally_kill': noob_meter_definitions['pl'],
        'player_ally_blowup': noob_meter_definitions['pl'],
        'player_squadman_hit': noob_meter_definitions['pl'],
        'player_squadman_kill': noob_meter_definitions['pl'],
        'player_squadman_blowup': noob_meter_definitions['pl'],
        'player_enemy_hit': noob_meter_definitions['pl'],
        'player_enemy_kill': noob_meter_definitions['pl'],
        'player_enemy_blowup': noob_meter_definitions['pl'],
        'player_allytk_hit': noob_meter_definitions['pl'],
        'player_allytk_kill': noob_meter_definitions['pl'],
        'player_allytk_blowup': noob_meter_definitions['pl'],
        'player_enemytk_hit': noob_meter_definitions['pl'],
        'player_enemytk_kill': noob_meter_definitions['pl'],
        'player_enemytk_blowup': noob_meter_definitions['pl']
    },
    'hp': [
        {'value': 201, 'color': noob_meter_definitions['colorHP']['very_low']},
        {'value': 401, 'color': noob_meter_definitions['colorHP']['low']},
        {'value': 1001, 'color': noob_meter_definitions['colorHP']['average']},
        {'value': 9999, 'color': noob_meter_definitions['colorHP']['above_average']}
    ],
    'hp_ratio': [
        {'value': 10, 'color': noob_meter_definitions['colorHP']['very_low']},
        {'value': 25, 'color': noob_meter_definitions['colorHP']['low']},
        {'value': 50, 'color': noob_meter_definitions['colorHP']['average']},
        {'value': 101, 'color': noob_meter_definitions['colorHP']['above_average']}
    ],
    'x': [
        {'value': 16.5, 'color': noob_meter_definitions['colorRating']['very_bad']},
        {'value': 33.5, 'color': noob_meter_definitions['colorRating']['bad']},
        {'value': 52.5, 'color': noob_meter_definitions['colorRating']['normal']},
        {'value': 75.5, 'color': noob_meter_definitions['colorRating']['good']},
        {'value': 92.5, 'color': noob_meter_definitions['colorRating']['very_good']},
        {'value': 999, 'color': noob_meter_definitions['colorRating']['unique']}
    ],
    'eff': [
        {'value': 615, 'color': noob_meter_definitions['colorRating']['very_bad']},
        {'value': 870, 'color': noob_meter_definitions['colorRating']['bad']},
        {'value': 1175, 'color': noob_meter_definitions['colorRating']['normal']},
        {'value': 1525, 'color': noob_meter_definitions['colorRating']['good']},
        {'value': 1850, 'color': noob_meter_definitions['colorRating']['very_good']},
        {'value': 9999, 'color': noob_meter_definitions['colorRating']['unique']}
    ],
    'wtr': [
        {'value': 2631, 'color': noob_meter_definitions['colorRating']['very_bad']},
        {'value': 4464, 'color': noob_meter_definitions['colorRating']['bad']},
        {'value': 6249, 'color': noob_meter_definitions['colorRating']['normal']},
        {'value': 8141, 'color': noob_meter_definitions['colorRating']['good']},
        {'value': 9460, 'color': noob_meter_definitions['colorRating']['very_good']},
        {'value': 99999, 'color': noob_meter_definitions['colorRating']['unique']}
    ],
    'wn8': [
        {'value': 300, 'color': noob_meter_definitions['colorRating']['very_bad']},
        {'value': 600, 'color': noob_meter_definitions['colorRating']['bad']},
        {'value': 900, 'color': noob_meter_definitions['colorRating']['b_average']},
        {'value': 1200, 'color': noob_meter_definitions['colorRating']['average']},
        {'value': 1500, 'color': noob_meter_definitions['colorRating']['good']},
        {'value': 1750, 'color': noob_meter_definitions['colorRating']['very_good']},
        {'value': 2300, 'color': noob_meter_definitions['colorRating']['great']},
        {'value': 2900, 'color': noob_meter_definitions['colorRating']['unique']},
        {'value': 9999, 'color': noob_meter_definitions['colorRating']['s_unique']}
    ],
    'wgr': [
        {'value': 2020, 'color': noob_meter_definitions['colorRating']['very_bad']},
        {'value': 4185, 'color': noob_meter_definitions['colorRating']['bad']},
        {'value': 6340, 'color': noob_meter_definitions['colorRating']['normal']},
        {'value': 8525, 'color': noob_meter_definitions['colorRating']['good']},
        {'value': 9930, 'color': noob_meter_definitions['colorRating']['very_good']},
        {'value': 99999, 'color': noob_meter_definitions['colorRating']['unique']}
    ],
    'e': [
        {'value': 3, 'color': noob_meter_definitions['colorRating']['very_bad']},
        {'value': 6, 'color': noob_meter_definitions['colorRating']['bad']},
        {'value': 7, 'color': noob_meter_definitions['colorRating']['normal']},
        {'value': 8, 'color': noob_meter_definitions['colorRating']['good']},
        {'value': 9, 'color': noob_meter_definitions['colorRating']['very_good']},
        {'value': 20, 'color': noob_meter_definitions['colorRating']['unique']}
    ],
    'winrate': [
        {'value': 43, 'color': noob_meter_definitions['colorRating']['very_bad']},
        {'value': 45, 'color': noob_meter_definitions['colorRating']['bad']},
        {'value': 47, 'color': noob_meter_definitions['colorRating']['average']},
        {'value': 51, 'color': noob_meter_definitions['colorRating']['normal']},
        {'value': 53, 'color': noob_meter_definitions['colorRating']['good']},
        {'value': 55, 'color': noob_meter_definitions['colorRating']['very_good']},
        {'value': 59, 'color': noob_meter_definitions['colorRating']['great']},
        {'value': 93, 'color': noob_meter_definitions['colorRating']['unique']},
        {'value': 101, 'color': noob_meter_definitions['colorRating']['s_unique']}
    ],
    'kb': [
        {'value': 2, 'color': noob_meter_definitions['colorRating']['very_bad']},
        {'value': 6, 'color': noob_meter_definitions['colorRating']['bad']},
        {'value': 16, 'color': noob_meter_definitions['colorRating']['normal']},
        {'value': 30, 'color': noob_meter_definitions['colorRating']['good']},
        {'value': 43, 'color': noob_meter_definitions['colorRating']['very_good']},
        {'value': 999, 'color': noob_meter_definitions['colorRating']['unique']}
    ],
    'avglvl': [
        {'value': 1, 'color': noob_meter_definitions['colorRating']['very_bad']},
        {'value': 2, 'color': noob_meter_definitions['colorRating']['bad']},
        {'value': 4, 'color': noob_meter_definitions['colorRating']['normal']},
        {'value': 6, 'color': noob_meter_definitions['colorRating']['good']},
        {'value': 8, 'color': noob_meter_definitions['colorRating']['very_good']},
        {'value': 10, 'color': noob_meter_definitions['colorRating']['unique']}
    ],
    't_battles': [
        {'value': 100, 'color': noob_meter_definitions['colorRating']['very_bad']},
        {'value': 250, 'color': noob_meter_definitions['colorRating']['bad']},
        {'value': 500, 'color': noob_meter_definitions['colorRating']['normal']},
        {'value': 1000, 'color': noob_meter_definitions['colorRating']['good']},
        {'value': 1800, 'color': noob_meter_definitions['colorRating']['very_good']},
        {'value': 99999, 'color': noob_meter_definitions['colorRating']['unique']}
    ],
    'tdb': [
        {'value': 500, 'color': noob_meter_definitions['colorRating']['very_bad']},
        {'value': 750, 'color': noob_meter_definitions['colorRating']['bad']},
        {'value': 1000, 'color': noob_meter_definitions['colorRating']['normal']},
        {'value': 1800, 'color': noob_meter_definitions['colorRating']['good']},
        {'value': 2500, 'color': noob_meter_definitions['colorRating']['very_good']},
        {'value': 9999, 'color': noob_meter_definitions['colorRating']['unique']}
    ],
    'tdv': [
        {'value': 0.6, 'color': noob_meter_definitions['colorRating']['very_bad']},
        {'value': 0.8, 'color': noob_meter_definitions['colorRating']['bad']},
        {'value': 1.0, 'color': noob_meter_definitions['colorRating']['normal']},
        {'value': 1.3, 'color': noob_meter_definitions['colorRating']['good']},
        {'value': 2.0, 'color': noob_meter_definitions['colorRating']['very_good']},
        {'value': 15, 'color': noob_meter_definitions['colorRating']['unique']}
    ],
    'tfb': [
        {'value': 0.6, 'color': noob_meter_definitions['colorRating']['very_bad']},
        {'value': 0.8, 'color': noob_meter_definitions['colorRating']['bad']},
        {'value': 1.0, 'color': noob_meter_definitions['colorRating']['normal']},
        {'value': 1.3, 'color': noob_meter_definitions['colorRating']['good']},
        {'value': 2.0, 'color': noob_meter_definitions['colorRating']['very_good']},
        {'value': 15, 'color': noob_meter_definitions['colorRating']['unique']}
    ],
    'tsb': [
        {'value': 0.6, 'color': noob_meter_definitions['colorRating']['very_bad']},
        {'value': 0.8, 'color': noob_meter_definitions['colorRating']['bad']},
        {'value': 1.0, 'color': noob_meter_definitions['colorRating']['normal']},
        {'value': 1.3, 'color': noob_meter_definitions['colorRating']['good']},
        {'value': 2.0, 'color': noob_meter_definitions['colorRating']['very_good']},
        {'value': 15, 'color': noob_meter_definitions['colorRating']['unique']}
    ],
    'wn8effd': [
        {'value': 0.6, 'color': noob_meter_definitions['colorRating']['very_bad']},
        {'value': 0.8, 'color': noob_meter_definitions['colorRating']['bad']},
        {'value': 1.0, 'color': noob_meter_definitions['colorRating']['normal']},
        {'value': 1.3, 'color': noob_meter_definitions['colorRating']['good']},
        {'value': 2.0, 'color': noob_meter_definitions['colorRating']['very_good']},
        {'value': 15, 'color': noob_meter_definitions['colorRating']['unique']}
    ],
    'dmg_ratio_player': [
        {'value': 16.5, 'color': noob_meter_definitions['colorRating']['very_bad']},
        {'value': 33.5, 'color': noob_meter_definitions['colorRating']['bad']},
        {'value': 49.5, 'color': noob_meter_definitions['colorRating']['normal']},
        {'value': 66.5, 'color': noob_meter_definitions['colorRating']['good']},
        {'value': 83.5, 'color': noob_meter_definitions['colorRating']['very_good']},
        {'value': 999, 'color': noob_meter_definitions['colorRating']['unique']}
    ],
    'damageRating': [
        {'value': 20, 'color': noob_meter_definitions['colorRating']['very_bad']},
        {'value': 60, 'color': noob_meter_definitions['colorRating']['bad']},
        {'value': 90, 'color': noob_meter_definitions['colorRating']['normal']},
        {'value': 99, 'color': noob_meter_definitions['colorRating']['good']},
        {'value': 99.9, 'color': noob_meter_definitions['colorRating']['very_good']},
        {'value': 101, 'color': noob_meter_definitions['colorRating']['unique']}
    ],
    'hitsRatio': [
        {'value': 47.5, 'color': noob_meter_definitions['colorRating']['very_bad']},
        {'value': 60.5, 'color': noob_meter_definitions['colorRating']['bad']},
        {'value': 68.5, 'color': noob_meter_definitions['colorRating']['normal']},
        {'value': 74.5, 'color': noob_meter_definitions['colorRating']['good']},
        {'value': 78.5, 'color': noob_meter_definitions['colorRating']['very_good']},
        {'value': 101, 'color': noob_meter_definitions['colorRating']['unique']}
    ]
}


# XVM: xvm_scale/colors.xc

xvm_definitions = {
    'al': '#22CC00',
    'sq': '#FFB964',
    'tk': '#00EAFF',
    'en': '#F50800',
    'pl': '#FFFF2A',
    'colorRating': {
        'very_bad': '#FE0E00',
        'bad': '#FE7903',
        'normal': '#F8F400',
        'good': '#60FF00',
        'very_good': '#02C9B3',
        'unique': '#D042F3'
    },
    'colorHP': {
        'very_low': '#FF0000',
        'low': '#DD4444',
        'average': '#FFCC22',
        'above_average': '#FCFCFC'
    }
}

xvm_colors = {
    'colorRating': xvm_definitions['colorRating'],
    'colorHP': xvm_definitions['colorHP'],
    'system': {
        'ally_alive': xvm_definitions['al'],
        'ally_dead': '#B8FFC1',
        'ally_blowedup': '#007700',
        'squadman_alive': xvm_definitions['sq'],
        'squadman_dead': '#CA7000',
        'squadman_blowedup': '#A45A00',
        'teamKiller_alive': xvm_definitions['tk'],
        'teamKiller_dead': '#097783',
        'teamKiller_blowedup': '#096A75',
        'enemy_alive': xvm_definitions['en'],
        'enemy_dead': '#E29188',
        'enemy_blowedup': '#5A0401',
        'ally_base': xvm_definitions['al'],
        'enemy_base': xvm_definitions['en']
    },
    'dmg_kind': {
        'attack': '#FFAA55',
        'fire': '#FF6655',
        'ramming': '#00CCCC',
        'world_collision': '#998855',
        'death_zone': '#CCCCCC',
        'drowning': '#CCCCCC',
        'other': '#CCCCCC'
    },
    'vtype': {
        'LT': '#53B329',
        'MT': '#1EA2D2',
        'HT': '#957D5B',
        'SPG': '#B87AB2',
        'TD': '#F13439',
        'premium': '#FFA804',
        'usePremiumColor': False
    },
    'spotted': {
        'neverSeen': '#000000',
        'lost': '#FF552A',
        'spotted': '#FFBB00',
        'dead': '#FFFFFF',
        'neverSeen_arty': '#000000',
        'lost_arty': '#D9D9D9',
        'spotted_arty': '#FFBB00',
        'dead_arty': '#FFFFFF'
    },
    'totalHP': {
        'bad': '#FF0000',
        'neutral': '#FFFFFF',
        'good': '#00FF00'
    },
    'damage': {
        'ally_ally_hit': xvm_definitions['tk'],
        'ally_ally_kill': xvm_definitions['tk'],
        'ally_ally_blowup': xvm_definitions['tk'],
        'ally_squadman_hit': xvm_definitions['tk'],
        'ally_squadman_kill': xvm_definitions['tk'],
        'ally_squadman_blowup': xvm_definitions['tk'],
        'ally_enemy_hit': xvm_definitions['en'],
        'ally_enemy_kill': xvm_definitions['en'],
        'ally_enemy_blowup': xvm_definitions['en'],
        'ally_allytk_hit': xvm_definitions['tk'],
        'ally_allytk_kill': xvm_definitions['tk'],
        'ally_allytk_blowup': xvm_definitions['tk'],
        'ally_enemytk_hit': xvm_definitions['en'],
        'ally_enemytk_kill': xvm_definitions['en'],
        'ally_enemytk_blowup': xvm_definitions['en'],
        'enemy_ally_hit': xvm_definitions['al'],
        'enemy_ally_kill': xvm_definitions['al'],
        'enemy_ally_blowup': xvm_definitions['al'],
        'enemy_squadman_hit': xvm_definitions['al'],
        'enemy_squadman_kill': xvm_definitions['al'],
        'enemy_squadman_blowup': xvm_definitions['al'],
        'enemy_enemy_hit': xvm_definitions['en'],
        'enemy_enemy_kill': xvm_definitions['en'],
        'enemy_enemy_blowup': xvm_definitions['en'],
        'enemy_allytk_hit': xvm_definitions['al'],
        'enemy_allytk_kill': xvm_definitions['al'],
        'enemy_allytk_blowup': xvm_definitions['al'],
        'enemy_enemytk_hit': xvm_definitions['en'],
        'enemy_enemytk_kill': xvm_definitions['en'],
        'enemy_enemytk_blowup': xvm_definitions['en'],
        'unknown_ally_hit': xvm_definitions['al'],
        'unknown_ally_kill': xvm_definitions['al'],
        'unknown_ally_blowup': xvm_definitions['al'],
        'unknown_squadman_hit': xvm_definitions['al'],
        'unknown_squadman_kill': xvm_definitions['al'],
        'unknown_squadman_blowup': xvm_definitions['al'],
        'unknown_enemy_hit': xvm_definitions['en'],
        'unknown_enemy_kill': xvm_definitions['en'],
        'unknown_enemy_blowup': xvm_definitions['en'],
        'unknown_allytk_hit': xvm_definitions['al'],
        'unknown_allytk_kill': xvm_definitions['al'],
        'unknown_allytk_blowup': xvm_definitions['al'],
        'unknown_enemytk_hit': xvm_definitions['en'],
        'unknown_enemytk_kill': xvm_definitions['en'],
        'unknown_enemytk_blowup': xvm_definitions['en'],
        'squadman_ally_hit': xvm_definitions['sq'],
        'squadman_ally_kill': xvm_definitions['sq'],
        'squadman_ally_blowup': xvm_definitions['sq'],
        'squadman_squadman_hit': xvm_definitions['sq'],
        'squadman_squadman_kill': xvm_definitions['sq'],
        'squadman_squadman_blowup': xvm_definitions['sq'],
        'squadman_enemy_hit': xvm_definitions['sq'],
        'squadman_enemy_kill': xvm_definitions['sq'],
        'squadman_enemy_blowup': xvm_definitions['sq'],
        'squadman_allytk_hit': xvm_definitions['sq'],
        'squadman_allytk_kill': xvm_definitions['sq'],
        'squadman_allytk_blowup': xvm_definitions['sq'],
        'squadman_enemytk_hit': xvm_definitions['sq'],
        'squadman_enemytk_kill': xvm_definitions['sq'],
        'squadman_enemytk_blowup': xvm_definitions['sq'],
        'player_ally_hit': xvm_definitions['pl'],
        'player_ally_kill': xvm_definitions['pl'],
        'player_ally_blowup': xvm_definitions['pl'],
        'player_squadman_hit': xvm_definitions['pl'],
        'player_squadman_kill': xvm_definitions['pl'],
        'player_squadman_blowup': xvm_definitions['pl'],
        'player_enemy_hit': xvm_definitions['pl'],
        'player_enemy_kill': xvm_definitions['pl'],
        'player_enemy_blowup': xvm_definitions['pl'],
        'player_allytk_hit': xvm_definitions['pl'],
        'player_allytk_kill': xvm_definitions['pl'],
        'player_allytk_blowup': xvm_definitions['pl'],
        'player_enemytk_hit': xvm_definitions['pl'],
        'player_enemytk_kill': xvm_definitions['pl'],
        'player_enemytk_blowup': xvm_definitions['pl']
    },
    'hp': [
        {'value': 200, 'color': xvm_definitions['colorHP']['very_low']},
        {'value': 400, 'color': xvm_definitions['colorHP']['low']},
        {'value': 1000, 'color': xvm_definitions['colorHP']['average']},
        {'value': 9999, 'color': xvm_definitions['colorHP']['above_average']}
    ],
    'hp_ratio': [
        {'value': 10.4, 'color': xvm_definitions['colorHP']['very_low']},
        {'value': 25.4, 'color': xvm_definitions['colorHP']['low']},
        {'value': 50.4, 'color': xvm_definitions['colorHP']['average']},
        {'value': 100, 'color': xvm_definitions['colorHP']['above_average']}
    ],
    'x': [
        {'value': 16.4, 'color': xvm_definitions['colorRating']['very_bad']},
        {'value': 33.4, 'color': xvm_definitions['colorRating']['bad']},
        {'value': 52.4, 'color': xvm_definitions['colorRating']['normal']},
        {'value': 75.4, 'color': xvm_definitions['colorRating']['good']},
        {'value': 92.4, 'color': xvm_definitions['colorRating']['very_good']},
        {'value': 999, 'color': xvm_definitions['colorRating']['unique']}
    ],
    'eff': [
        {'value': 598, 'color': xvm_definitions['colorRating']['very_bad']},
        {'value': 874, 'color': xvm_definitions['colorRating']['bad']},
        {'value': 1079, 'color': xvm_definitions['colorRating']['normal']},
        {'value': 1540, 'color': xvm_definitions['colorRating']['good']},
        {'value': 1868, 'color': xvm_definitions['colorRating']['very_good']},
        {'value': 9999, 'color': xvm_definitions['colorRating']['unique']}
    ],
    'wtr': [
        {'value': 2631, 'color': xvm_definitions['colorRating']['very_bad']},
        {'value': 4464, 'color': xvm_definitions['colorRating']['bad']},
        {'value': 6249, 'color': xvm_definitions['colorRating']['normal']},
        {'value': 8141, 'color': xvm_definitions['colorRating']['good']},
        {'value': 9460, 'color': xvm_definitions['colorRating']['very_good']},
        {'value': 99999, 'color': xvm_definitions['colorRating']['unique']}
    ],
    'wn8': [
        {'value': 397, 'color': xvm_definitions['colorRating']['very_bad']},
        {'value': 914, 'color': xvm_definitions['colorRating']['bad']},
        {'value': 1489, 'color': xvm_definitions['colorRating']['normal']},
        {'value': 2231, 'color': xvm_definitions['colorRating']['good']},
        {'value': 2979, 'color': xvm_definitions['colorRating']['very_good']},
        {'value': 9999, 'color': xvm_definitions['colorRating']['unique']}
    ],
    'winrate': [
        {'value': 46.49, 'color': xvm_definitions['colorRating']['very_bad']},
        {'value': 48.49, 'color': xvm_definitions['colorRating']['bad']},
        {'value': 52.49, 'color': xvm_definitions['colorRating']['normal']},
        {'value': 57.49, 'color': xvm_definitions['colorRating']['good']},
        {'value': 64.49, 'color': xvm_definitions['colorRating']['very_good']},
        {'value': 100, 'color': xvm_definitions['colorRating']['unique']}
    ],
    'kb': [
        {'value': 2, 'color': xvm_definitions['colorRating']['very_bad']},
        {'value': 6, 'color': xvm_definitions['colorRating']['bad']},
        {'value': 16, 'color': xvm_definitions['colorRating']['normal']},
        {'value': 30, 'color': xvm_definitions['colorRating']['good']},
        {'value': 43, 'color': xvm_definitions['colorRating']['very_good']},
        {'value': 999, 'color': xvm_definitions['colorRating']['unique']}
    ],
    'avglvl': [
        {'value': 1, 'color': xvm_definitions['colorRating']['very_bad']},
        {'value': 2, 'color': xvm_definitions['colorRating']['bad']},
        {'value': 4, 'color': xvm_definitions['colorRating']['normal']},
        {'value': 6, 'color': xvm_definitions['colorRating']['good']},
        {'value': 8, 'color': xvm_definitions['colorRating']['very_good']},
        {'value': 10, 'color': xvm_definitions['colorRating']['unique']}
    ],
    't_battles': [
        {'value': 99, 'color': xvm_definitions['colorRating']['very_bad']},
        {'value': 249, 'color': xvm_definitions['colorRating']['bad']},
        {'value': 499, 'color': xvm_definitions['colorRating']['normal']},
        {'value': 999, 'color': xvm_definitions['colorRating']['good']},
        {'value': 1799, 'color': xvm_definitions['colorRating']['very_good']},
        {'value': 99999, 'color': xvm_definitions['colorRating']['unique']}
    ],
    'tdb': [
        {'value': 499, 'color': xvm_definitions['colorRating']['very_bad']},
        {'value': 749, 'color': xvm_definitions['colorRating']['bad']},
        {'value': 999, 'color': xvm_definitions['colorRating']['normal']},
        {'value': 1799, 'color': xvm_definitions['colorRating']['good']},
        {'value': 2499, 'color': xvm_definitions['colorRating']['very_good']},
        {'value': 9999, 'color': xvm_definitions['colorRating']['unique']}
    ],
    'tdv': [
        {'value': 0.5, 'color': xvm_definitions['colorRating']['very_bad']},
        {'value': 0.7, 'color': xvm_definitions['colorRating']['bad']},
        {'value': 0.9, 'color': xvm_definitions['colorRating']['normal']},
        {'value': 1.2, 'color': xvm_definitions['colorRating']['good']},
        {'value': 1.9, 'color': xvm_definitions['colorRating']['very_good']},
        {'value': 15, 'color': xvm_definitions['colorRating']['unique']}
    ],
    'tfb': [
        {'value': 0.5, 'color': xvm_definitions['colorRating']['very_bad']},
        {'value': 0.7, 'color': xvm_definitions['colorRating']['bad']},
        {'value': 0.9, 'color': xvm_definitions['colorRating']['normal']},
        {'value': 1.2, 'color': xvm_definitions['colorRating']['good']},
        {'value': 1.9, 'color': xvm_definitions['colorRating']['very_good']},
        {'value': 15, 'color': xvm_definitions['colorRating']['unique']}
    ],
    'tsb': [
        {'value': 0.5, 'color': xvm_definitions['colorRating']['very_bad']},
        {'value': 0.7, 'color': xvm_definitions['colorRating']['bad']},
        {'value': 0.9, 'color': xvm_definitions['colorRating']['normal']},
        {'value': 1.2, 'color': xvm_definitions['colorRating']['good']},
        {'value': 1.9, 'color': xvm_definitions['colorRating']['very_good']},
        {'value': 15, 'color': xvm_definitions['colorRating']['unique']}
    ],
    'wn8effd': [
        {'value': 0.5, 'color': xvm_definitions['colorRating']['very_bad']},
        {'value': 0.7, 'color': xvm_definitions['colorRating']['bad']},
        {'value': 0.9, 'color': xvm_definitions['colorRating']['normal']},
        {'value': 1.2, 'color': xvm_definitions['colorRating']['good']},
        {'value': 1.9, 'color': xvm_definitions['colorRating']['very_good']},
        {'value': 15, 'color': xvm_definitions['colorRating']['unique']}
    ],
    'dmg_ratio_player': [
        {'value': 16.5, 'color': xvm_definitions['colorRating']['very_bad']},
        {'value': 33.5, 'color': xvm_definitions['colorRating']['bad']},
        {'value': 49.5, 'color': xvm_definitions['colorRating']['normal']},
        {'value': 66.5, 'color': xvm_definitions['colorRating']['good']},
        {'value': 83.5, 'color': xvm_definitions['colorRating']['very_good']},
        {'value': 999, 'color': xvm_definitions['colorRating']['unique']}
    ],
    'damageRating': [
        {'value': 64.99, 'color': xvm_definitions['colorRating']['very_bad']},
        {'value': 84.99, 'color': xvm_definitions['colorRating']['normal']},
        {'value': 94.99, 'color': xvm_definitions['colorRating']['good']},
        {'value': 100, 'color': xvm_definitions['colorRating']['unique']}
    ],
    'hitsRatio': [
        {'value': 47.4, 'color': xvm_definitions['colorRating']['very_bad']},
        {'value': 60.4, 'color': xvm_definitions['colorRating']['bad']},
        {'value': 68.4, 'color': xvm_definitions['colorRating']['normal']},
        {'value': 74.4, 'color': xvm_definitions['colorRating']['good']},
        {'value': 78.4, 'color': xvm_definitions['colorRating']['very_good']},
        {'value': 100, 'color': xvm_definitions['colorRating']['unique']}
    ]
}


# WotLabs: wotlabs_scale/colors.xc

wot_labs_definitions = {
    'al': '#22CC00',
    'sq': '#FFB964',
    'tk': '#00EAFF',
    'en': '#F50800',
    'pl': '#FFFF2A',
    'colorRating': {
        'nocolor': '#CCCCCC',
        'very_bad': '#BB0000',
        'bad': '#FF0000',
        'b_average': '#FF6600',
        'average': '#F8F400',
        'normal': '#F8F400',
        'good': '#99CC00',
        'very_good': '#00CC00',
        'great': '#66BBFF',
        'unique': '#CC66CC',
        's_unique': '#FF00FF'
    },
    'colorRatingNew': {
        'beginner': '#C00B00',
        'basic': '#f11919',
        'below_average': '#ff8a00',
        'average': '#e6df27',
        'above_average': '#77e812',
        'good': '#459300',
        'very_good': '#2ae4ff',
        'great': '#00a0b8',
        'unicum': '#c64cff',
        'super_unicum': '#8225ad'
    },
    'colorHP': {
        'very_low': '#FF0000',
        'low': '#DD4444',
        'average': '#FFCC22',
        'above_average': '#FCFCFC'
    }
}

# Source winrate refers to three missing colorRating names.
# below_average, above_average and super_unicum use colorRatingNew.

wot_labs_colors = {
    'colorRating': wot_labs_definitions['colorRating'],
    'colorRatingNew': wot_labs_definitions['colorRatingNew'],
    'colorHP': wot_labs_definitions['colorHP'],
    'system': {
        'ally_alive': wot_labs_definitions['al'],
        'ally_dead': '#B8FFC1',
        'ally_blowedup': '#007700',
        'squadman_alive': wot_labs_definitions['sq'],
        'squadman_dead': '#CA7000',
        'squadman_blowedup': '#A45A00',
        'teamKiller_alive': wot_labs_definitions['tk'],
        'teamKiller_dead': '#097783',
        'teamKiller_blowedup': '#096A75',
        'enemy_alive': wot_labs_definitions['en'],
        'enemy_dead': '#E29188',
        'enemy_blowedup': '#5A0401',
        'ally_base': wot_labs_definitions['al'],
        'enemy_base': wot_labs_definitions['en']
    },
    'dmg_kind': {
        'attack': '#FFAA55',
        'fire': '#FF6655',
        'ramming': '#00CCCC',
        'world_collision': '#998855',
        'death_zone': '#CCCCCC',
        'drowning': '#CCCCCC',
        'other': '#CCCCCC'
    },
    'vtype': {
        'LT': '#53B329',
        'MT': '#1EA2D2',
        'HT': '#957D5B',
        'SPG': '#B87AB2',
        'TD': '#F13439',
        'premium': '#FFA804',
        'usePremiumColor': False
    },
    'spotted': {
        'neverSeen': '#000000',
        'lost': '#D9D9D9',
        'spotted': '#FFBB00',
        'dead': '#FFFFFF',
        'neverSeen_arty': '#000000',
        'lost_arty': '#D9D9D9',
        'spotted_arty': '#FFBB00',
        'dead_arty': '#FFFFFF'
    },
    'totalHP': {
        'bad': '#FF0000',
        'neutral': '#FFFFFF',
        'good': '#00FF00'
    },
    'damage': {
        'ally_ally_hit': wot_labs_definitions['tk'],
        'ally_ally_kill': wot_labs_definitions['tk'],
        'ally_ally_blowup': wot_labs_definitions['tk'],
        'ally_squadman_hit': wot_labs_definitions['tk'],
        'ally_squadman_kill': wot_labs_definitions['tk'],
        'ally_squadman_blowup': wot_labs_definitions['tk'],
        'ally_enemy_hit': wot_labs_definitions['en'],
        'ally_enemy_kill': wot_labs_definitions['en'],
        'ally_enemy_blowup': wot_labs_definitions['en'],
        'ally_allytk_hit': wot_labs_definitions['tk'],
        'ally_allytk_kill': wot_labs_definitions['tk'],
        'ally_allytk_blowup': wot_labs_definitions['tk'],
        'ally_enemytk_hit': wot_labs_definitions['en'],
        'ally_enemytk_kill': wot_labs_definitions['en'],
        'ally_enemytk_blowup': wot_labs_definitions['en'],
        'enemy_ally_hit': wot_labs_definitions['al'],
        'enemy_ally_kill': wot_labs_definitions['al'],
        'enemy_ally_blowup': wot_labs_definitions['al'],
        'enemy_squadman_hit': wot_labs_definitions['al'],
        'enemy_squadman_kill': wot_labs_definitions['al'],
        'enemy_squadman_blowup': wot_labs_definitions['al'],
        'enemy_enemy_hit': wot_labs_definitions['en'],
        'enemy_enemy_kill': wot_labs_definitions['en'],
        'enemy_enemy_blowup': wot_labs_definitions['en'],
        'enemy_allytk_hit': wot_labs_definitions['al'],
        'enemy_allytk_kill': wot_labs_definitions['al'],
        'enemy_allytk_blowup': wot_labs_definitions['al'],
        'enemy_enemytk_hit': wot_labs_definitions['en'],
        'enemy_enemytk_kill': wot_labs_definitions['en'],
        'enemy_enemytk_blowup': wot_labs_definitions['en'],
        'unknown_ally_hit': wot_labs_definitions['al'],
        'unknown_ally_kill': wot_labs_definitions['al'],
        'unknown_ally_blowup': wot_labs_definitions['al'],
        'unknown_squadman_hit': wot_labs_definitions['al'],
        'unknown_squadman_kill': wot_labs_definitions['al'],
        'unknown_squadman_blowup': wot_labs_definitions['al'],
        'unknown_enemy_hit': wot_labs_definitions['en'],
        'unknown_enemy_kill': wot_labs_definitions['en'],
        'unknown_enemy_blowup': wot_labs_definitions['en'],
        'unknown_allytk_hit': wot_labs_definitions['al'],
        'unknown_allytk_kill': wot_labs_definitions['al'],
        'unknown_allytk_blowup': wot_labs_definitions['al'],
        'unknown_enemytk_hit': wot_labs_definitions['en'],
        'unknown_enemytk_kill': wot_labs_definitions['en'],
        'unknown_enemytk_blowup': wot_labs_definitions['en'],
        'squadman_ally_hit': wot_labs_definitions['sq'],
        'squadman_ally_kill': wot_labs_definitions['sq'],
        'squadman_ally_blowup': wot_labs_definitions['sq'],
        'squadman_squadman_hit': wot_labs_definitions['sq'],
        'squadman_squadman_kill': wot_labs_definitions['sq'],
        'squadman_squadman_blowup': wot_labs_definitions['sq'],
        'squadman_enemy_hit': wot_labs_definitions['sq'],
        'squadman_enemy_kill': wot_labs_definitions['sq'],
        'squadman_enemy_blowup': wot_labs_definitions['sq'],
        'squadman_allytk_hit': wot_labs_definitions['sq'],
        'squadman_allytk_kill': wot_labs_definitions['sq'],
        'squadman_allytk_blowup': wot_labs_definitions['sq'],
        'squadman_enemytk_hit': wot_labs_definitions['sq'],
        'squadman_enemytk_kill': wot_labs_definitions['sq'],
        'squadman_enemytk_blowup': wot_labs_definitions['sq'],
        'player_ally_hit': wot_labs_definitions['pl'],
        'player_ally_kill': wot_labs_definitions['pl'],
        'player_ally_blowup': wot_labs_definitions['pl'],
        'player_squadman_hit': wot_labs_definitions['pl'],
        'player_squadman_kill': wot_labs_definitions['pl'],
        'player_squadman_blowup': wot_labs_definitions['pl'],
        'player_enemy_hit': wot_labs_definitions['pl'],
        'player_enemy_kill': wot_labs_definitions['pl'],
        'player_enemy_blowup': wot_labs_definitions['pl'],
        'player_allytk_hit': wot_labs_definitions['pl'],
        'player_allytk_kill': wot_labs_definitions['pl'],
        'player_allytk_blowup': wot_labs_definitions['pl'],
        'player_enemytk_hit': wot_labs_definitions['pl'],
        'player_enemytk_kill': wot_labs_definitions['pl'],
        'player_enemytk_blowup': wot_labs_definitions['pl']
    },
    'hp': [
        {'value': 201, 'color': wot_labs_definitions['colorHP']['very_low']},
        {'value': 401, 'color': wot_labs_definitions['colorHP']['low']},
        {'value': 1001, 'color': wot_labs_definitions['colorHP']['average']},
        {'value': 9999, 'color': wot_labs_definitions['colorHP']['above_average']}
    ],
    'hp_ratio': [
        {'value': 10, 'color': wot_labs_definitions['colorHP']['very_low']},
        {'value': 25, 'color': wot_labs_definitions['colorHP']['low']},
        {'value': 50, 'color': wot_labs_definitions['colorHP']['average']},
        {'value': 101, 'color': wot_labs_definitions['colorHP']['above_average']}
    ],
    'x': [
        {'value': 16.5, 'color': wot_labs_definitions['colorRating']['very_bad']},
        {'value': 33.5, 'color': wot_labs_definitions['colorRating']['bad']},
        {'value': 52.5, 'color': wot_labs_definitions['colorRating']['normal']},
        {'value': 75.5, 'color': wot_labs_definitions['colorRating']['good']},
        {'value': 92.5, 'color': wot_labs_definitions['colorRating']['very_good']},
        {'value': 999, 'color': wot_labs_definitions['colorRating']['unique']}
    ],
    'eff': [
        {'value': 610, 'color': wot_labs_definitions['colorRating']['very_bad']},
        {'value': 850, 'color': wot_labs_definitions['colorRating']['bad']},
        {'value': 1145, 'color': wot_labs_definitions['colorRating']['normal']},
        {'value': 1475, 'color': wot_labs_definitions['colorRating']['good']},
        {'value': 1775, 'color': wot_labs_definitions['colorRating']['very_good']},
        {'value': 9999, 'color': wot_labs_definitions['colorRating']['unique']}
    ],
    'wtr': [
        {'value': 2631, 'color': wot_labs_definitions['colorRating']['very_bad']},
        {'value': 4464, 'color': wot_labs_definitions['colorRating']['bad']},
        {'value': 6249, 'color': wot_labs_definitions['colorRating']['normal']},
        {'value': 8141, 'color': wot_labs_definitions['colorRating']['good']},
        {'value': 9460, 'color': wot_labs_definitions['colorRating']['very_good']},
        {'value': 99999, 'color': wot_labs_definitions['colorRating']['unique']}
    ],
    'wn8': [
        {'value': 300, 'color': wot_labs_definitions['colorRatingNew']['beginner']},
        {'value': 450, 'color': wot_labs_definitions['colorRatingNew']['basic']},
        {'value': 650, 'color': wot_labs_definitions['colorRatingNew']['below_average']},
        {'value': 900, 'color': wot_labs_definitions['colorRatingNew']['average']},
        {'value': 1200, 'color': wot_labs_definitions['colorRatingNew']['above_average']},
        {'value': 1600, 'color': wot_labs_definitions['colorRatingNew']['good']},
        {'value': 2000, 'color': wot_labs_definitions['colorRatingNew']['very_good']},
        {'value': 2450, 'color': wot_labs_definitions['colorRatingNew']['great']},
        {'value': 2900, 'color': wot_labs_definitions['colorRatingNew']['unicum']},
        {'value': 9999, 'color': wot_labs_definitions['colorRatingNew']['super_unicum']}
    ],
    'wgr': [
        {'value': 2000, 'color': wot_labs_definitions['colorRating']['very_bad']},
        {'value': 4000, 'color': wot_labs_definitions['colorRating']['bad']},
        {'value': 6000, 'color': wot_labs_definitions['colorRating']['normal']},
        {'value': 8000, 'color': wot_labs_definitions['colorRating']['good']},
        {'value': 10000, 'color': wot_labs_definitions['colorRating']['very_good']},
        {'value': 20000, 'color': wot_labs_definitions['colorRating']['unique']}
    ],
    'e': [
        {'value': 3, 'color': wot_labs_definitions['colorRating']['very_bad']},
        {'value': 6, 'color': wot_labs_definitions['colorRating']['bad']},
        {'value': 7, 'color': wot_labs_definitions['colorRating']['normal']},
        {'value': 8, 'color': wot_labs_definitions['colorRating']['good']},
        {'value': 9, 'color': wot_labs_definitions['colorRating']['very_good']},
        {'value': 20, 'color': wot_labs_definitions['colorRating']['unique']}
    ],
    'winrate': [
        {'value': 46, 'color': wot_labs_definitions['colorRating']['very_bad']},
        {'value': 47, 'color': wot_labs_definitions['colorRating']['bad']},
        {'value': 48, 'color': wot_labs_definitions['colorRatingNew']['below_average']},
        {'value': 50, 'color': wot_labs_definitions['colorRating']['average']},
        {'value': 52, 'color': wot_labs_definitions['colorRatingNew']['above_average']},
        {'value': 54, 'color': wot_labs_definitions['colorRating']['good']},
        {'value': 56, 'color': wot_labs_definitions['colorRating']['very_good']},
        {'value': 60, 'color': wot_labs_definitions['colorRating']['great']},
        {'value': 65, 'color': wot_labs_definitions['colorRating']['unique']},
        {'value': 101, 'color': wot_labs_definitions['colorRatingNew']['super_unicum']}
    ],
    'kb': [
        {'value': 2, 'color': wot_labs_definitions['colorRating']['very_bad']},
        {'value': 5, 'color': wot_labs_definitions['colorRating']['bad']},
        {'value': 9, 'color': wot_labs_definitions['colorRating']['normal']},
        {'value': 14, 'color': wot_labs_definitions['colorRating']['good']},
        {'value': 20, 'color': wot_labs_definitions['colorRating']['very_good']},
        {'value': 999, 'color': wot_labs_definitions['colorRating']['unique']}
    ],
    'avglvl': [
        {'value': 2, 'color': wot_labs_definitions['colorRating']['very_bad']},
        {'value': 3, 'color': wot_labs_definitions['colorRating']['bad']},
        {'value': 5, 'color': wot_labs_definitions['colorRating']['normal']},
        {'value': 7, 'color': wot_labs_definitions['colorRating']['good']},
        {'value': 9, 'color': wot_labs_definitions['colorRating']['very_good']},
        {'value': 11, 'color': wot_labs_definitions['colorRating']['unique']}
    ],
    't_battles': [
        {'value': 100, 'color': wot_labs_definitions['colorRating']['very_bad']},
        {'value': 250, 'color': wot_labs_definitions['colorRating']['bad']},
        {'value': 500, 'color': wot_labs_definitions['colorRating']['normal']},
        {'value': 1000, 'color': wot_labs_definitions['colorRating']['good']},
        {'value': 1800, 'color': wot_labs_definitions['colorRating']['very_good']},
        {'value': 99999, 'color': wot_labs_definitions['colorRating']['unique']}
    ],
    'tdb': [
        {'value': 500, 'color': wot_labs_definitions['colorRating']['very_bad']},
        {'value': 1000, 'color': wot_labs_definitions['colorRating']['normal']},
        {'value': 1800, 'color': wot_labs_definitions['colorRating']['good']},
        {'value': 2500, 'color': wot_labs_definitions['colorRating']['very_good']},
        {'value': 3000, 'color': wot_labs_definitions['colorRating']['unique']}
    ],
    'tdv': [
        {'value': 0.6, 'color': wot_labs_definitions['colorRating']['very_bad']},
        {'value': 0.8, 'color': wot_labs_definitions['colorRating']['bad']},
        {'value': 1.0, 'color': wot_labs_definitions['colorRating']['normal']},
        {'value': 1.3, 'color': wot_labs_definitions['colorRating']['good']},
        {'value': 2.0, 'color': wot_labs_definitions['colorRating']['very_good']},
        {'value': 15, 'color': wot_labs_definitions['colorRating']['unique']}
    ],
    'tfb': [
        {'value': 0.6, 'color': wot_labs_definitions['colorRating']['very_bad']},
        {'value': 0.8, 'color': wot_labs_definitions['colorRating']['bad']},
        {'value': 1.0, 'color': wot_labs_definitions['colorRating']['normal']},
        {'value': 1.3, 'color': wot_labs_definitions['colorRating']['good']},
        {'value': 2.0, 'color': wot_labs_definitions['colorRating']['very_good']},
        {'value': 15, 'color': wot_labs_definitions['colorRating']['unique']}
    ],
    'tsb': [
        {'value': 0.6, 'color': wot_labs_definitions['colorRating']['very_bad']},
        {'value': 0.8, 'color': wot_labs_definitions['colorRating']['bad']},
        {'value': 1.0, 'color': wot_labs_definitions['colorRating']['normal']},
        {'value': 1.3, 'color': wot_labs_definitions['colorRating']['good']},
        {'value': 2.0, 'color': wot_labs_definitions['colorRating']['very_good']},
        {'value': 15, 'color': wot_labs_definitions['colorRating']['unique']}
    ],
    'wn8effd': [
        {'value': 0.6, 'color': wot_labs_definitions['colorRating']['very_bad']},
        {'value': 0.8, 'color': wot_labs_definitions['colorRating']['bad']},
        {'value': 1.0, 'color': wot_labs_definitions['colorRating']['normal']},
        {'value': 1.3, 'color': wot_labs_definitions['colorRating']['good']},
        {'value': 2.0, 'color': wot_labs_definitions['colorRating']['very_good']},
        {'value': 15, 'color': wot_labs_definitions['colorRating']['unique']}
    ],
    'dmg_ratio_player': [
        {'value': 16.5, 'color': wot_labs_definitions['colorRating']['very_bad']},
        {'value': 33.5, 'color': wot_labs_definitions['colorRating']['bad']},
        {'value': 49.5, 'color': wot_labs_definitions['colorRating']['normal']},
        {'value': 66.5, 'color': wot_labs_definitions['colorRating']['good']},
        {'value': 83.5, 'color': wot_labs_definitions['colorRating']['very_good']},
        {'value': 999, 'color': wot_labs_definitions['colorRating']['unique']}
    ],
    'damageRating': [
        {'value': 64.99, 'color': wot_labs_definitions['colorRating']['very_bad']},
        {'value': 84.99, 'color': wot_labs_definitions['colorRating']['normal']},
        {'value': 94.99, 'color': wot_labs_definitions['colorRating']['good']},
        {'value': 100, 'color': wot_labs_definitions['colorRating']['unique']}
    ],
    'hitsRatio': [
        {'value': 47.5, 'color': wot_labs_definitions['colorRating']['very_bad']},
        {'value': 60.5, 'color': wot_labs_definitions['colorRating']['bad']},
        {'value': 68.5, 'color': wot_labs_definitions['colorRating']['normal']},
        {'value': 74.5, 'color': wot_labs_definitions['colorRating']['good']},
        {'value': 78.5, 'color': wot_labs_definitions['colorRating']['very_good']},
        {'value': 100, 'color': wot_labs_definitions['colorRating']['unique']}
    ]
}


# Project statistics absent from XVM: keep all limits and palette decisions here.
MOE_LEVELS = (0, 20, 40, 55, 65, 85, 95, 100)
for _table in (noob_meter_colors, xvm_colors, wot_labs_colors):
    _palette = _table['colorRating']
    _table['mog'] = [{'value': limit, 'color': _palette.get(name, _palette['unique']) if name != 'neutral' else '#FFFFFF'} for limit, name in zip(MOE_LEVELS, ('neutral', 'very_bad', 'bad', 'normal', 'good', 'very_good', 'unique', 's_unique'))]
    for _metric in ('damageRatio', 'damageHP', 'relativePerformance'):
        _table[_metric] = [{'value': limit, 'color': _palette[name]} for limit, name in zip((0.5, 0.75, 1.0, 1.5, 2.0, 1e30), ('very_bad', 'bad', 'normal', 'good', 'very_good', 'unique'))]
    _table['diff'] = [
        {'value': 0, 'color': _palette['very_bad']},
        {'value': 0, 'color': _palette['normal']},
        {'value': 1e30, 'color': _palette['good']}
    ]
del _table, _palette, _metric


color_tables = [
    ColorRating('NoobMeter', noob_meter_colors).table(),
    ColorRating('XVM', xvm_colors).table(),
    ColorRating('WotLabs', wot_labs_colors).table()
]


def getRatingColors(index=0):
    """Return a configured palette, falling back to NoobMeter for invalid settings."""
    try:
        index = int(index)
    except (TypeError, ValueError, OverflowError):
        index = 0
    if not 0 <= index < len(color_tables):
        index = 0
    return color_tables[index]['colors']


def getColor(data, ratting_color, value=None, kwargs=None):
    """
    Get a color based on a rating value from a color configuration.
    data (dict): Color configuration data.
    ratting_color (str): Rating category key.
    value (float, optional): Value to compare against thresholds. Defaults to None.
    kwargs (float, optional): Alternative value for 'x' category. Defaults to None.
    str: Color in hex format or None if not found.
    """
    aliases = {'xwn8': 'x', 'xeff': 'x', 'xte': 'x', 'dmg': 'tdb',
               'winRate': 'winrate', 't_winrate': 'winrate', 'hitRate': 'hitsRatio',
               'avgDamage': 'tdb', 'avgFrags': 'tfb', 'avgSpotted': 'tsb',
               'marks': 'mog', 'battles': 'kb'}
    category = ratting_color if ratting_color in data else aliases.get(ratting_color, ratting_color)
    if value is None and kwargs is not None:
        category, value = 'x', kwargs
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if math.isnan(value) or math.isinf(value):
        return None
    if ratting_color == 'battles' and category == 'kb':
        value /= 1000.0
    bands = data.get(category)
    if not isinstance(bands, (list, tuple)) or not bands:
        return None
    if category == 'diff':
        return formatColor(bands[0 if value < 0 else 2 if value > 0 else 1]['color'])
    if category == 'mog':
        for item in reversed(bands):
            if value >= item['value']:
                return formatColor(item['color'])
        return formatColor(bands[0]['color'])
    for item in bands:
        if value < item['value']:
            return formatColor(item['color'])
    # The last source limit is a sentinel, not a reason to lose the rating color.
    return formatColor(bands[-1]['color'])


def formatColor(color):
    """
    Format a color string to a standard hex format.
    color (str): Color string, possibly starting with '0x'.
    str: Color in standard hex format (#RRGGBB).
    """
    return '#' + color[2:] if color.startswith('0x') else color


def getRatingPaletteColor(name, index=0):
    """Resolve named statistical colors and missing-data colors centrally."""
    palette = getRatingColors(index)['colorRating']
    name = {'super_unique': 's_unique', 'not_available': 'nocolor'}.get(name, name)
    if name == 's_unique':
        return palette.get(name, palette['unique'])
    return palette.get(name, palette.get('nocolor', '#CCCCCC'))


def getStatisticColor(metric, value, index=0):
    """Public mod API: always returns a valid color, including missing statistics."""
    return getColor(getRatingColors(index), metric, value) or getRatingPaletteColor('nocolor', index)


def getComparisonColor(value, reference, index=0):
    """Color a statistical comparison using the selected palette."""
    try:
        difference = float(value) - float(reference)
    except (TypeError, ValueError, OverflowError):
        difference = None
    return getStatisticColor('diff', difference, index)


def getMoeDamageColor(damage, targets, index=0):
    """Color damage against the seven calculated MoE targets (20 through 100)."""
    try:
        damage = float(damage)
    except (TypeError, ValueError, OverflowError):
        return getRatingPaletteColor('nocolor', index)
    if math.isnan(damage) or math.isinf(damage) or len(targets) != 7:
        return getRatingPaletteColor('nocolor', index)
    for percent, target in zip(MOE_LEVELS[1:], targets):
        if damage <= target:
            return getStatisticColor('mog', percent, index)
    return getStatisticColor('mog', 100, index)
