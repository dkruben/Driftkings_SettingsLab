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
        // '#' starts a URL fragment; the carousel colour images are named '#rrggbb.png'.
        return (window.DK_GAME_ROOT || 'coui://') + path.replace(/#/g, '%23');
    }

    DK.asset = asset;
    DK.assets = {
        mapTopDown: 'gui/maps/icons/map/05_prohorovka.png',          // Prokhorovka, 1000 m
        battleScene: 'gui/maps/icons/map/stats/05_prohorovka.png',
        hangarTank: 'gui/maps/shop/vehicles/600x450/A12_T32.png',
        favorite: 'gui/maps/icons/library/favorite_small.png',
        flag: function (nation) { return 'gui/maps/icons/flags/160x100/' + nation + '.png'; },
        tank: function (id) { return 'gui/maps/icons/vehicle/420x307/' + id + '.png'; },
        type: function (type) { return 'gui/maps/icons/vehicleTypes/24x24/' + type + '.png'; },
        level: function (level) { return 'gui/maps/icons/levels/tank_level_' + level + '.png'; },
        mastery: function (grade) { return 'gui/maps/icons/library/proficiency/class_icons_' + grade + '.png'; },
        marks: function (count) { return 'gui/maps/icons/library/marksOnGun/mark_' + count + '.png'; }
    };
}());
