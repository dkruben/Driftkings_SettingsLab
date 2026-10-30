/* DK Settings — imagens do cliente usadas nas pré-visualizações.
   No jogo lêem-se diretamente dos pacotes com coui:// (nada é copiado para o .wotmod).
   A pré-visualização no browser define DK_GAME_ROOT para as cópias locais extraídas por
   ferramentas/extrair_imagens.py; a lista abaixo tem de coincidir com a dessa ferramenta. */
(function () {
    'use strict';
    var DK = window.DK;

    // Resource path ('gui/...', 'img://gui/...' or 'coui://gui/...') -> URL the view can load.
    function asset(path) {
        if (!path) { return ''; }
        path = String(path).replace(/^img:\/\//, '').replace(/^coui:\/\//, '').replace(/^\.?\//, '');
        if (/^[a-z]+:/i.test(path) || /(^|\/)\.\.(\/|$)/.test(path) || path.indexOf('\\')>=0) { return ''; }
        // '#' starts a URL fragment; carousel colour images use '#rrggbb' filenames.
        return (window.DK_GAME_ROOT || 'coui://') + path.replace(/#/g, '%23');
    }

    // Real vehicles for the live previews, read from the client's definitions (wot-src EU 2.4.1):
    // item_defs/vehicles/<nation>/list.xml (tier, class) and <vehicle>.xml (hull + top turret HP, vision),
    // short names from text/lc_messages/<nation>_vehicles.po. T32 is the player's vehicle.
    function vehicle(id, name, level, vtype, maxHp) { return {id: id, vehicle: name, level: level, vtype: vtype, maxHp: maxHp}; }
    var T32 = vehicle('usa:A12_T32', 'T32', 8, 'heavyTank', 1650);
    T32.view = 390;          // Turret_2_A12_T32 circularVisionRadius
    T32.shellRange = 720;    // _105mm_Gun_T5E1_32 shots maxDistance
    DK.sample = {
        player: T32,
        // A tier X battle's enemy team (15 vehicles), for team totals such as the High Caliber target.
        enemies: [
            vehicle('ussr:R45_IS-7', 'IS-7', 10, 'heavyTank', 2400), vehicle('france:F108_Panhard_EBR_105', 'EBR 105', 10, 'lightTank', 1500),
            vehicle('uk:GB31_Conqueror_Gun', 'Conqueror GC', 10, 'SPG', 530), vehicle('ussr:R97_Object_140', 'Obj. 140', 10, 'mediumTank', 1950),
            vehicle('sweden:S11_Strv_103B', 'Strv 103B', 10, 'AT-SPG', 1800), vehicle('usa:A69_T110E5', 'T110E5', 10, 'heavyTank', 2200),
            vehicle('france:F18_Bat_Chatillon25t', 'B-C 25 t', 10, 'mediumTank', 1800), vehicle('china:Ch22_113', '113', 10, 'heavyTank', 2300),
            vehicle('ussr:R19_IS-3', 'IS-3', 8, 'heavyTank', 1650), vehicle('uk:GB70_N_FV4202_105', 'FV4202', 8, 'mediumTank', 1400),
            vehicle('germany:G56_E-100', 'E 100', 10, 'heavyTank', 2700), vehicle('germany:G89_Leopard1', 'Leopard 1', 10, 'mediumTank', 1850),
            vehicle('germany:G121_Grille_15_L63', 'Grille 15', 10, 'AT-SPG', 1800), vehicle('italy:It13_Progetto_M35_mod_46', 'Progetto 46', 8, 'mediumTank', 1400),
            vehicle('usa:A12_T32', 'T32', 8, 'heavyTank', 1650)
        ],
        // Class abbreviations as the battle shows them (VMText.formatText).
        types: {lightTank: 'LT', mediumTank: 'MT', heavyTank: 'HT', 'AT-SPG': 'TD', SPG: 'SPG'},
        find: function (name) {
            var list = DK.sample.enemies;
            for (var i = 0; i < list.length; i++) { if (list[i].vehicle === name) { return list[i]; } }
            return null;
        },
        // Client minimap constants: AOI.VEHICLE_CIRCULAR_AOI_RADIUS, VISIBILITY.MAX_RADIUS / MIN_RADIUS,
        // and CIRCLE_STYLE.COLOR (minimap/settings.py), which the mod keeps while circle colours are unchanged.
        circles: {draw: 565, maxView: 445, proximity: 50},
        circleColors: {draw: '#FFFF00', maxView: '#FFFFFF', view: '#27FF27', proximity: '#44A8AE'}
    };

    DK.asset = asset;
    DK.assets = {
        mapTopDown: 'gui/maps/icons/map/05_prohorovka.png',          // Prokhorovka, 1000 m
        battleScene: 'gui/maps/icons/map/stats/05_prohorovka.png',
        hangarTank: 'gui/maps/shop/vehicles/600x450/A12_T32.png',
        favorite: 'gui/maps/icons/library/favorite_small.png',
        flag: function (nation) { return 'gui/maps/icons/hangar/carousel/cards/flags/x400x300/' + nation + '.png'; },
        tank: function (id) { return 'gui/maps/icons/vehicle/420x307/' + id + '.png'; },
        type: function (type) { return 'gui/maps/icons/vehicleTypes/24x24/' + type + '.png'; },
        level: function (level) { return 'gui/maps/icons/levels/tank_level_' + level + '.png'; },
        mastery: function (grade) { return 'gui/maps/icons/library/proficiency/class_icons_' + grade + '.png'; },
        marks: function (count) { return 'gui/maps/icons/library/marksOnGun/mark_' + count + '.png'; }
    };
}());
