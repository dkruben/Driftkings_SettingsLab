(function () {
    'use strict';
    var K=window.__dkMarksKit, root=K.node('div','dk-mog dk-mog--compact',document.body);
    var header=K.node('div','dk-mog__header',root), brand=K.node('div','dk-mog__brand',header);
    K.node('span','dk-mog__logo',brand,'///'); var title=K.node('span','',brand,'');
    var context=K.node('span','dk-mog__context',header);
    var overview=K.node('div','dk-mog__overview',root);
    var hero=K.node('div','dk-mog__hero',overview), main=K.node('div','',hero);
    var estimatedLabel=K.node('div','dk-mog__label',main), percentRow=K.node('div','dk-mog__percentrow',main);
    var estimated=K.node('div','dk-mog__percent',percentRow), trend=K.node('span','dk-mog__trend',percentRow);
    var starRow=K.node('div','',hero), stars=K.stars(starRow);
    var unavailable=K.node('div','dk-mog__unavailable',root);
    var metrics=K.node('div','dk-mog__metrics',overview), cards=[];
    ['combined','target','needed'].forEach(function(key){
        var card=K.node('div','dk-mog__metric dk-mog__metric--'+key,metrics);
        cards.push({root:card,label:K.node('div','dk-mog__label',card),value:K.node('span','dk-mog__value',card)});
    });
    var progress=K.node('div','dk-mog__progress',root), scale=K.scale(progress);
    var next=K.node('div','dk-mog__next',progress), nextLabel=K.node('span','',next), gap=K.node('span','',next);
    var footer=K.node('div','dk-mog__footer',root), current=K.node('span','',footer);
    function render(data) {
        var cfg=data.config||{}, valid=data.state==='data', mini=cfg.miniMode!==false;
        var interactive=cfg.draggable===true && cfg.locked===false;
        root.className='dk-mog dk-mog--compact'+(mini?' dk-mog--mini':'')+(valid?'':' dk-mog--empty')+(interactive?' dk-mog--unlocked':'');
        var accent=K.theme(root,cfg,true,mini?400:650);
        K.setLocale(cfg);
        K.style(root,'zIndex','10000');
        K.style(root,'pointerEvents',interactive?'auto':'none');
        K.style(root.firstChild,'pointerEvents',interactive?'auto':'none');
        K.style(root.firstChild,'cursor',interactive?'move':'default');
        K.text(title,K.label(data,'title',''));
        // Replays have no dossier: borrowed or base data is flagged so it is never read as the player's mark.
        var approximate=valid&&data.approximate===true;
        K.text(context,approximate?K.label(data,'approximate',''):K.label(data,'battle',''));
        K.text(estimatedLabel,K.label(data,'estimated',''));
        K.text(estimated,valid?(approximate?'~':'')+K.percent(data.estimatedMark):'\u2014'); K.style(estimated,'color',accent);
        K.show(starRow,cfg.showStars!==false); K.updateStars(stars,data.marksAchieved||0);
        K.show(unavailable,!valid); K.text(unavailable,data.message||K.label(data,'unavailable',''));
        ['combined','target','needed'].forEach(function(key,i){ K.text(cards[i].label,K.label(data,key,'')); });
        K.text(cards[0].value,K.formatted(data.combinedDamage));
        K.text(cards[1].value,valid?K.formatted(data.targetDamage):'\u2014'); K.text(cards[2].value,valid?K.formatted(data.damageNeeded):'\u2014');
        K.style(cards[2].value,'color',accent);
        K.show(cards[0].root,cfg.showCombined!==false); K.show(cards[1].root,cfg.showTargetDamage!==false); K.show(cards[2].root,cfg.showRequiredDamage!==false);
        K.show(metrics,cfg.showCombined!==false||cfg.showTargetDamage!==false||cfg.showRequiredDamage!==false);
        K.show(progress,valid&&cfg.showProgress!==false); scale.update(data.estimatedMark,data.marksAchieved,data.currentMark);
        K.style(scale.fill,'backgroundImage','linear-gradient(0deg,'+accent+',#fff1ab)');
        K.text(nextLabel,data.completed?K.label(data,'completed',''):K.label(data,'next','')+' '+data.nextMilestone+'%');
        K.text(gap,data.completed?'':K.formatted(data.gap,2)+' '+K.label(data,'gapUnit','')+' '+K.label(data,'remaining',''));
        K.text(current,K.label(data,'current','')+': '+K.percent(data.currentMark));
        K.text(trend,(data.trend||{}).text||'\u2014'); trend.className='dk-mog__trend dk-mog__trend--'+((data.trend||{}).direction||'unknown');
        K.show(trend,valid&&cfg.showTrend!==false);
    }
    K.connect('DriftkingsMarksOnGunBattle','__dkBattleMarks',root,render,K.position,K.savedPosition);
}());
