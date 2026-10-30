(function () {
    'use strict';
    var K = window.__dkMarksKit, root = K.node('div', 'dk-mog dk-mog--full', document.body);
    var header = K.node('div', 'dk-mog__header', root), brand = K.node('div', 'dk-mog__brand', header);
    K.node('span', 'dk-mog__logo', brand, '///'); var title=K.node('span', '', brand, '');
    var context = K.node('span', 'dk-mog__context', header);
    var vehicle = K.node('div', 'dk-mog__vehicle', root);
    var hero = K.node('div', 'dk-mog__hero', root), main = K.node('div', '', hero);
    var currentLabel = K.node('div', 'dk-mog__label', main), current = K.node('div', 'dk-mog__percent', main);
    var starsRow = K.node('div', '', hero), stars = K.stars(starsRow);
    var unavailable = K.node('div', 'dk-mog__unavailable', root);
    var progress = K.node('div', 'dk-mog__progress', root), scale = K.scale(progress);
    var next = K.node('div', 'dk-mog__next', progress), nextLabel = K.node('span', '', next), gap = K.node('span', '', next);
    var metrics = K.node('div', 'dk-mog__metrics', root), cards = [];
    ['ema', 'target', 'needed'].forEach(function (name) {
        var card = K.node('div', 'dk-mog__metric', metrics);
        cards.push({label:K.node('div','dk-mog__label',card),value:K.node('span','dk-mog__value',card)});
    });
    var note = K.node('div', 'dk-mog__note', root);
    var history = K.node('div', 'dk-mog__history', root), historyLabel = K.node('div', 'dk-mog__label', history);
    var chart = K.graph(history), historyInfo = K.node('div','dk-mog__muted',history), range = K.node('div','dk-mog__muted',history);
    var advanced = K.node('div','dk-mog__footer',root), averages = K.node('span','',advanced), achievements = K.node('span','',advanced);
    function render(data, resized) {
        var cfg=data.config||{}, milestone=data.milestone||{}, valid=data.state==='data' && (data.target||{}).eligible;
        root.className='dk-mog dk-mog--full'+(cfg.compactMode?' dk-mog--dense':'')+(valid?'':' dk-mog--empty');
        K.setLocale(cfg);
        K.style(root,'zIndex','10000');
        K.style(root,'pointerEvents','auto');
        K.style(header,'cursor',cfg.locked?'default':'move');
        var accent=K.theme(root,cfg,false);
        K.text(title,K.label(data,'title',''));
        K.text(context, K.label(data,'hangar',''));
        K.text(currentLabel,K.label(data,'current',''));
        K.text(vehicle,(data.vehicle||'\u2014')+(K.roman(data.tier)?' · '+K.roman(data.tier):'')+(data.nation?' · '+data.nation:''));
        K.show(vehicle,cfg.showVehicleInfo!==false);
        K.text(current,valid?K.percent(data.currentMark):'\u2014'); K.style(current,'color',accent);
        K.updateStars(stars,valid?data.displayMarks:0);
        K.show(unavailable,!valid); K.text(unavailable,data.message||K.label(data,'unavailable',''));
        K.show(progress,valid&&(cfg.showProgress!==false||cfg.showMilestones!==false));
        scale.update(data.currentMark,data.displayMarks,null,cfg.showMilestones!==false);
        K.show(scale.fill,cfg.showProgress!==false); K.show(next,cfg.showProgress!==false);
        K.style(scale.fill,'backgroundImage','linear-gradient(0deg,'+accent+',#fff1ab)');
        K.text(nextLabel,milestone.completed?K.label(data,'completed',''):K.label(data,'next','')+' '+milestone.nextMilestone+'%');
        K.text(gap,milestone.completed?'':K.formatted(milestone.gap,2)+' '+K.label(data,'gapUnit','')+' '+K.label(data,'remaining',''));
        K.show(metrics,valid&&cfg.showDamageStatistics!==false);
        ['ema','expected','needed'].forEach(function(key,i){ K.text(cards[i].label,K.label(data,key,'')); });
        K.text(cards[2].label,K.label(data,'emaGap',''));
        if ((data.target||{}).threshold && !milestone.completed) { K.text(cards[1].label,K.label(data,'expected','')+' ('+data.target.threshold+'%)'); }
        K.text(cards[0].value,K.formatted(data.movingAverage));
        K.text(cards[1].value,K.formatted(data.targetDamage)); K.text(cards[2].value,K.formatted(data.damageNeeded));
        K.style(cards[2].value,'color',accent);
        K.text(note,K.label(data,'estimateNote','')); K.show(note,valid&&cfg.showDamageStatistics!==false);
        K.show(history,valid&&cfg.showHistory!==false);
        K.text(historyLabel,K.label(data,'history',''));
        var samples=(data.recent||{}).samples||[], sufficient=samples.length>=2;
        K.show(chart.element,sufficient);
        if (resized) { chart.invalidate(); }
        if (sufficient&&!cfg.compactMode&&cfg.showHistory!==false&&valid) { chart.draw(samples); }
        K.text(historyInfo,sufficient?K.label(data,'historyNote',''):K.label(data,'waiting',''));
        // Warhelios has no arrow glyph; » is in the font.
        K.text(range,sufficient?samples[0].battles+' » '+samples[samples.length-1].battles+' · '+K.percent(samples[0].percent)+' » '+K.percent(samples[samples.length-1].percent):'');
        K.show(advanced,valid&&cfg.showAdvancedStatistics!==false);
        K.text(averages,K.label(data,'direct','')+': '+K.formatted(data.averageDirect)+' · '+K.label(data,'assist','')+': '+K.formatted(data.averageAssist));
        K.text(achievements,'WN8 '+(data.wn8||'\u2014')+' · '+(data.winRate||'\u2014')+' · '+(data.mastery||'\u2014'));
    }
    K.connect('DriftkingsMarksOnGunHangar','__dkHangarMarks',root,render,K.position,K.savedPosition);
}());
