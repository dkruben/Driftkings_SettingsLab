# -*- coding: utf-8 -*-
"""Descriptive section names, with aliases for existing profiles and translations."""
import re

from driftkings._constants import VEHICLE_MARKERS

LEGACY_NAMES = {'VehicleMarkers': VEHICLE_MARKERS.NAME,
 'AccountManager': 'account_manager',
 'AimingAngles': 'gun_traverse_limits',
 'ArcadeZoom': 'third_person_zoom',
 'ArmorCalculator': 'penetration_indicator',
 'ArtySplash': 'artillery_blast_radius',
 'AutoAimOptimize': 'autoaim_target_indicator',
 'AutoClaimClan': 'clan_reward_collection',
 'BanksLoader': 'sound_bank_loader',
 'BattleEfficiency': 'battle_performance',
 'BattleOptions': 'battle_preferences',
 'BattleStat': 'battle_statistics',
 'CarouselStats': 'vehicle_carousel',
 'CrewSettings': 'crew_management',
 'DispersionCircle': 'aiming_reticles',
 'DispersionTimer': 'aiming_countdown',
 'DistanceMarker': 'target_distance',
 'driftkings': 'driftkings',
 'FlightTimer': 'shell_flight_time',
 'HangarOptions': 'hangar_preferences',
 'InfoPanel': 'target_information',
 'LogsSwapper': 'game_log_manager',
 'MainGun': 'high_caliber_progress',
 'MarksOnGunBattle': 'battle_marks_of_excellence',
 'MarksOnGunHangar': 'hangar_marks_of_excellence',
 'MarksOnGunTechTree': 'tech_tree_marks_of_excellence',
 'MinimapPlugins': 'minimap_enhancements',
 'OwnHealth': 'vehicle_health',
 'PlayerPanelPro': 'team_panels',
 'RepairExtended': 'repair_controls',
 'ServerTurretExtended': 'server_turret_sync',
 'SixthSense': 'sixth_sense_alert',
 'SpottedExtendedLight': 'enemy_spotting_status',
 'Stats': 'stats',
 'ZoomExtended': 'sniper_camera'}
PREVIOUS_SECTIONS = {'aiming_angles': 'gun_traverse_limits',
 'arcade_zoom': 'third_person_zoom',
 'armor_calculator': 'penetration_indicator',
 'arty_splash': 'artillery_blast_radius',
 'auto_aim_optimize': 'autoaim_target_indicator',
 'auto_claim_clan': 'clan_reward_collection',
 'banks_loader': 'sound_bank_loader',
 'battle_efficiency': 'battle_performance',
 'battle_options': 'battle_preferences',
 'battle_stat': 'battle_statistics',
 'carousel_stats': 'vehicle_carousel',
 'crew_settings': 'crew_management',
 'dispersion_circle': 'aiming_reticles',
 'dispersion_timer': 'aiming_countdown',
 'distance_marker': 'target_distance',
 'flight_timer': 'shell_flight_time',
 'hangar_options': 'hangar_preferences',
 'info_panel': 'target_information',
 'logs_swapper': 'game_log_manager',
 'main_gun': 'high_caliber_progress',
 'marks_on_gun_battle': 'battle_marks_of_excellence',
 'marks_on_gun_hangar': 'hangar_marks_of_excellence',
 'marks_on_gun_tech_tree': 'tech_tree_marks_of_excellence',
 'minimap_plugins': 'minimap_enhancements',
 'own_health': 'vehicle_health',
 'player_panel_pro': 'team_panels',
 'repair_extended': 'repair_controls',
 'server_turret_extended': 'server_turret_sync',
 'sixth_sense': 'sixth_sense_alert',
 'spotted_extended_light': 'enemy_spotting_status',
 'zoom_extended': 'sniper_camera'}
COMPONENT_NAMES = {'VehicleMarkers': VEHICLE_MARKERS.NAME,
 'AccountManager': 'account_manager',
 'AimingCountdown': 'aiming_countdown',
 'AimingReticles': 'aiming_reticles',
 'ArtilleryBlastRadius': 'artillery_blast_radius',
 'AutoaimTargetIndicator': 'autoaim_target_indicator',
 'BattleMarksOfExcellence': 'battle_marks_of_excellence',
 'BattlePerformance': 'battle_performance',
 'BattlePreferences': 'battle_preferences',
 'BattleStatistics': 'battle_statistics',
 'ClanRewardCollection': 'clan_reward_collection',
 'CrewManagement': 'crew_management',
 'EnemySpottingStatus': 'enemy_spotting_status',
 'GameLogManager': 'game_log_manager',
 'GunTraverseLimits': 'gun_traverse_limits',
 'HangarMarksOfExcellence': 'hangar_marks_of_excellence',
 'HangarPreferences': 'hangar_preferences',
 'HighCaliberProgress': 'high_caliber_progress',
 'Main': 'main',
 'MinimapEnhancements': 'minimap_enhancements',
 'PenetrationIndicator': 'penetration_indicator',
 'RepairControls': 'repair_controls',
 'ServerTurretSync': 'server_turret_sync',
 'ShellFlightTime': 'shell_flight_time',
 'SixthSenseAlert': 'sixth_sense_alert',
 'SniperCamera': 'sniper_camera',
 'SoundBankLoader': 'sound_bank_loader',
 'TargetDistance': 'target_distance',
 'TargetInformation': 'target_information',
 'TeamPanels': 'team_panels',
 'TechTreeMarksOfExcellence': 'tech_tree_marks_of_excellence',
 'ThirdPersonZoom': 'third_person_zoom',
 'VehicleCarousel': 'vehicle_carousel',
 'VehicleHealth': 'vehicle_health'}
SECTIONS = tuple(sorted(set(name for old, name in LEGACY_NAMES.items() if old not in ('driftkings', 'Stats'))))
PREVIOUS_NAMES = dict((name, old) for old, name in LEGACY_NAMES.items())


def section_name(value):
    name = value.NAME if hasattr(value, 'NAME') else value
    name = COMPONENT_NAMES.get(name, LEGACY_NAMES.get(name, PREVIOUS_SECTIONS.get(name, name)))
    if not isinstance(name, (str, type(u''))) or not re.match(r'^[a-z][a-z0-9_]*\Z', name):
        raise ValueError('Invalid settings section: ' + str(name))
    return name


def previous_name(value):
    name = section_name(value)
    return PREVIOUS_NAMES.get(name, name)
