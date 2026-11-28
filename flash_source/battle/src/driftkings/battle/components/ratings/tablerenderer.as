package driftkings.battle.components.ratings
{
    import flash.display.DisplayObject;
    import flash.display.DisplayObjectContainer;
    import flash.display.Shape;
    import flash.geom.Matrix;
    import flash.geom.Point;
    import flash.text.TextField;
    import flash.text.TextFormat;
    import flash.utils.Dictionary;
    public class tablerenderer
    {
        // Dark substrate behind the loading table: black at this opacity at its solid core. The exterior edges fade
        // out over BG_FADE px beyond the occupied content; the inner edge fades over at most half the centre gap.
        private static const BG_ALPHA:Number=0.65;
        private static const BG_PAD:Number=6;
        private static const BG_FADE:Number=24;
        // Overflow fallback: when the normal gutter does not fit the viewport, the gutter is compacted to this value.
        private static const COMPACT_GAP:Number=2;
        private var substrates:Dictionary=new Dictionary(true);
        private var headers:Dictionary=new Dictionary(true);
        public var layoutCompactAlly:int=0;
        public var layoutCompactEnemy:int=0;
        public var layoutHeaderDeltaAlly:Number=0;
        public var layoutHeaderDeltaEnemy:Number=0;
        public var layoutBgFade:Number=0;
        public var layoutPushCount:int=0;
        public var layoutPushAlly:int=0;
        public var layoutPushEnemy:int=0;
        public var layoutExteriorAlly:Number=0;
        public var layoutExteriorEnemy:Number=0;
        public var layoutOverlayAlly:int=0;
        public var layoutOverlayEnemy:int=0;
        public var layoutIndependentAlly:int=0;
        public var layoutIndependentEnemy:int=0;
        public var layoutConflictAlly:int=0;
        public var layoutConflictEnemy:int=0;
        public var layoutHeaderIcons:int=0;
        private var state:nativestate;
        private var extra:extrafields;
        public var matched:int=0;
        public function tablerenderer(s:nativestate,e:extrafields) { state=s; extra=e; }
        private function at(owner:Object,key:String,index:int):Object
        { return key in owner && owner[key] && index>=0 && index<owner[key].length ? owner[key][index] : null; }
        public function drawFrontline(owner:Object,payload:Object,screen:String):void
        {
            // Lists recycle renderers while scrolling and filtering by sector. Resolve
            // their current DAAPI identity every draw, never their visible row index.
            var ids:Object={}, accounts:Object={};
            for each (var row:Object in payload.rows)
            {
                ids[row.id]=row;
                if (row.accountDBID>0)
                {
                    var account:String=String(row.accountDBID);
                    accounts[account]=accounts.hasOwnProperty(account) ? null : row;
                }
            }
            frontlineList(owner.team1PlayerList as DisplayObjectContainer,ids,accounts,screen);
            frontlineList(owner.team2PlayerList as DisplayObjectContainer,ids,accounts,screen);
        }
        private function frontlineList(list:DisplayObjectContainer,ids:Object,accounts:Object,screen:String):void
        {
            if (!list) return;
            for (var i:int=0;i<list.numChildren;++i)
            {
                var child:DisplayObject=list.getChildAt(i), renderer:Object=child;
                if (!child.visible) continue;
                if ("getData" in renderer && renderer.getData is Function &&
                    (screen=="tab" ? "playerName" in renderer && "vehicleName" in renderer : "textField" in renderer && "vehicleField" in renderer))
                {
                    var data:Object=renderer.getData();
                    if (!data) continue;
                    var row:Object=ids[data.vehicleID];
                    if (!row && data.accountDBID>0) row=accounts[String(data.accountDBID)];
                    if (!row || data.accountDBID>0 && row.accountDBID!=data.accountDBID) continue;
                    var cfg:Object=row[screen];
                    if (!cfg || !cfg.enabled) continue;
                    var nick:TextField=(screen=="tab" ? renderer.playerName : renderer.textField) as TextField;
                    var vehicle:TextField=(screen=="tab" ? renderer.vehicleName : renderer.vehicleField) as TextField;
                    var side:String=row.ally ? "Left" : "Right";
                    frontlineText(nick,cfg["format"+side+"Nick"],cfg.nameFieldShowBorder);
                    frontlineText(vehicle,cfg["format"+side+"Vehicle"],cfg.vehicleFieldShowBorder);
                    if (screen=="tab") frontlineText(renderer.frags as TextField,cfg["format"+side+"Frags"],cfg.fragsFieldShowBorder);
                    ++matched;
                }
                else if (child is DisplayObjectContainer) frontlineList(child as DisplayObjectContainer,ids,accounts,screen);
            }
        }
        private function frontlineText(field:TextField,text:*,border:*):void
        {
            if (!field || !state.base(field,"visible") || text===null || text===undefined) return;
            // Native widths/positions leave room for ranks, lives and sector icons.
            extra.drawText(field,String(text),field.x,field.width,nativestate.flag(border),true);
            state.setValue(field,"visible",false);
        }
        // Loading-screen columns: one shared width per logical column (nick, vehicle) measured from the rendered
        // formatted text, anchored outward from the native inner edges. TAB and frontline never use this path.
        // Widths are re-measured only when the payload, screen or effective text format changes; the placement
        // arithmetic is recomputed from native base positions each draw, so nothing accumulates.
        private static const LAYOUT_GUTTER:Number=6;
        private static const LAYOUT_GAP:Number=4;
        private static const LAYOUT_MARGIN:Number=4;
        private var measurer:TextField=new TextField();
        private var widthCache:Object=null;
        // Vehicle column reservation: the largest width seen for this view and configuration. It never shrinks while
        // the view lives, so asynchronous rating data cannot make the table contract and expand again.
        private var reservedVehicle:Number=0;
        private var reservationOwner:Object=null;
        private var reservationKey:String="";
        private var cacheOwner:Object=null;
        private var cachePayload:Object=null;
        private var cacheKey:String="";
        private var cacheRows:int=-1;
        // Layout state of the last pass (shared anchors, reservations, overflow). Read by no other component.
        public var layoutRevision:int=0;
        public var layoutNickW:Number=0;
        public var layoutVehicleW:Number=0;
        public var layoutOverflow:Number=0;
        public var layoutLimitLeft:Number=0;
        public var layoutLimitRight:Number=0;
        public var layoutVehicleActual:Number=0;
        public var layoutReservedVehicle:Number=0;
        public var layoutPrestigeW:Number=0;
        public var layoutClassW:Number=0;
        public var layoutAnchorAlly:Number=0;
        public var layoutAnchorEnemy:Number=0;
        public var layoutRowsUnavailable:int=0;
        public var layoutPrestigeAnchorAlly:Number=0;
        public var layoutPrestigeAnchorEnemy:Number=0;
        public var layoutClassAnchorAlly:Number=0;
        public var layoutClassAnchorEnemy:Number=0;
        public var layoutVehicleLeftAlly:Number=0;
        public var layoutVehicleLeftEnemy:Number=0;
        public var layoutOuterAlly:Number=0;
        public var layoutOuterEnemy:Number=0;
        public var layoutBadgeW:Number=0;
        public var layoutSquadW:Number=0;
        public var layoutBgAllyX0:Number=0;
        public var layoutBgAllyX1:Number=0;
        public var layoutBgEnemyX0:Number=0;
        public var layoutBgEnemyX1:Number=0;
        public var layoutBgY0:Number=0;
        public var layoutBgY1:Number=0;
        public var layoutExtraCollisions:int=0;
        public var layoutExtraSpan:Number=0;
        private function measureHtml(value:*,format:TextFormat):Number
        {
            if (value===null || value===undefined) return 0;
            var html:String=String(value);
            if (html.length==0) return 0;
            measurer.embedFonts=false; measurer.multiline=false; measurer.wordWrap=false; measurer.autoSize="none";
            if (format) measurer.defaultTextFormat=format;
            measurer.htmlText=html;
            return measurer.textWidth+LAYOUT_GUTTER;
        }
        private function measureRaw(value:*,format:TextFormat):Number
        {
            if (value===null || value===undefined || String(value).length==0) return 0;
            measurer.embedFonts=false; measurer.multiline=false; measurer.wordWrap=false; measurer.autoSize="none";
            if (format) measurer.defaultTextFormat=format;
            measurer.htmlText=String(value);
            return measurer.textWidth;
        }
        private static const HIDDEN_STATS:RegExp=/size=['"]0['"]/;
        private function sizedStats(html:String):String
        {
            return html.replace(/size='0'/g,"size='13'").replace(/size="0"/g,'size="13"');
        }
        private function configSignature(cfg:Object):String
        {
            if (!cfg) return "";
            return [cfg.vehicleFieldOffsetXLeft,cfg.vehicleFieldOffsetXRight,cfg.vehicleFieldWidthDeltaLeft,
                    cfg.vehicleFieldWidthDeltaRight,cfg.nameFieldWidthDeltaLeft,cfg.nameFieldWidthDeltaRight,
                    cfg.removePrestigeLevel,cfg.vehicleIconOffsetXLeft,cfg.vehicleIconOffsetXRight].join("|");
        }
        private function maxWidthOf(owner:Object,name:String):Number
        {
            var list:Object=owner[name], widest:Number=0;
            if (!list) return 0;
            for (var i:int=0;i<list.length;++i)
            {
                var item:DisplayObject=list[i] as DisplayObject;
                if (item && item.visible && item.width>widest) widest=item.width;
            }
            return widest;
        }
        // Shared contour anchor: the outer edge of the contour column. Ally: the leftmost contour edge; enemy: the
        // rightmost. Contours keep their own widths, so the anchor is the common edge of the column.
        // Occupied bounds relative to the element origin. Native components are not all origin-left: the left-side
        // prestige and some contours extend towards negative x from their origin. Measured from the current x, the
        // offset does not change when the element is moved, so it is safe to use after placement.
        private function occupiedOffset(item:DisplayObject):Number
        {
            if (!item || !item.parent) return 0;
            var box:*=item.getBounds(item.parent);
            return Number(box.x)-item.x;
        }
        private function loadingAnchor(owner:Object,suffix:String,sign:int,shift:Number):Number
        {
            var icons:Object=owner["vehicleIcons"+suffix], anchor:Number=0, found:Boolean=false;
            if (!icons) return NaN;
            for (var i:int=0;i<icons.length;++i)
            {
                var icon:DisplayObject=icons[i] as DisplayObject;
                if (!icon || !icon.visible) continue;
                var iconLeft:Number=state.base(icon,"x")+shift+occupiedOffset(icon);
                var outer:Number=sign>0 ? iconLeft : iconLeft+icon.width;
                if (!found) anchor=outer;
                else anchor=sign>0 ? Math.min(anchor,outer) : Math.max(anchor,outer);
                found=true;
            }
            return found ? anchor : NaN;
        }
        // Column geometry for one side, from the shared anchor and the shared column widths. Nothing here depends on
        // a row's own text, so every row of a side uses the same vertical anchors. Independent extra-field bands
        // push the cursor outward; overlay fields and the fields themselves are never moved.
        private function loadingGeometry(owner:Object,suffix:String,sign:int,widths:Object,limits:Object,gapSize:Number):Object
        {
            var sample:Object=widths.sample, left:Boolean=sign>0;
            var side:String=left ? "Left" : "Right";
            var shift:Number=sign*nativestate.number(sample ? sample["vehicleIconOffsetX"+side] : 0);
            var anchor:Number=loadingAnchor(owner,suffix,sign,shift);
            var prestige:Number=Number(widths.prestige), klass:Number=Number(widths.klass);
            var vehicle:Number=Number(widths.vehicle), nick:Number=Number(widths.nick);
            var badge:Number=Number(widths.badge), squad:Number=Number(widths.squad);
            var geo:Object={valid:!isNaN(anchor), anchor:anchor, prestigeAnchor:0, classAnchor:0, vehicleLeft:0,
                            nickLeft:0, nickEdge:0, outerEdge:0, exteriorEdge:0, overflow:0, bands:[]};
            if (!geo.valid) return geo;
            var outward:int=-sign, gap:Number=gapSize;
            var pushesBefore:int=layoutPushCount;
            var contour:Number=maxWidthOf(owner,"vehicleIcons"+suffix);
            var bands:Array=extraBands(owner,widths,left,anchor,contour);
            geo.bands=bands;
            // One cursor walks outward from the contour. Each present column takes its shared width plus one gap;
            // columns with width 0 (disabled) take no space. "Inner" is the edge facing the contour.
            var cursor:Number=anchor-sign*gap;
            cursor=pushClear(cursor,prestige,outward,bands,gap);
            geo.prestigeAnchor=cursor;
            if (prestige>0) cursor+=outward*(prestige+gap);
            cursor=pushClear(cursor,klass,outward,bands,gap);
            geo.classAnchor=cursor;
            if (klass>0) cursor+=outward*(klass+gap);
            cursor=pushClear(cursor,vehicle,outward,bands,gap);
            geo.vehicleLeft=left ? cursor-vehicle : cursor;
            cursor+=outward*(vehicle+gap);
            cursor=pushClear(cursor,nick,outward,bands,gap);
            geo.nickLeft=left ? cursor-nick : cursor;
            geo.nickEdge=left ? geo.nickLeft : geo.nickLeft+nick;
            // Badges, then squads, continue outward from the nick column's outer edge. Shared columns, one gap each.
            cursor=geo.nickEdge+outward*gap;
            cursor=pushClear(cursor,badge,outward,bands,gap);
            geo.badgeAnchor=cursor;
            cursor+=outward*(badge>0 ? badge+gap : 0);
            cursor=pushClear(cursor,squad,outward,bands,gap);
            geo.squadAnchor=cursor;
            var outer:Number=geo.nickEdge;
            if (badge>0) outer=geo.badgeAnchor+outward*badge;
            if (squad>0) outer=geo.squadAnchor+outward*squad;
            geo.outerEdge=outer;
            // Exterior edge: the outermost occupied edge of the table and of its independent fields.
            var exterior:Number=outer;
            for each (var band:Object in bands)
                exterior=left ? Math.min(exterior,Number(band.lo)) : Math.max(exterior,Number(band.hi));
            geo.exteriorEdge=exterior;
            geo.overflow=left ? Math.max(0,Number(limits.left)-exterior) : Math.max(0,exterior-Number(limits.right));
            layoutBadgeW=badge; layoutSquadW=squad;
            if (left)
            {
                layoutAnchorAlly=anchor; layoutPrestigeAnchorAlly=geo.prestigeAnchor; layoutClassAnchorAlly=geo.classAnchor;
                layoutVehicleLeftAlly=geo.vehicleLeft; layoutOuterAlly=outer; layoutExteriorAlly=exterior;
                layoutPushAlly=layoutPushCount-pushesBefore;
            }
            else
            {
                layoutAnchorEnemy=anchor; layoutPrestigeAnchorEnemy=geo.prestigeAnchor; layoutClassAnchorEnemy=geo.classAnchor;
                layoutVehicleLeftEnemy=geo.vehicleLeft; layoutOuterEnemy=outer; layoutExteriorEnemy=exterior;
                layoutPushEnemy=layoutPushCount-pushesBefore;
            }
            return geo;
        }
        // Extra-field occupancy for one side, in owner coordinates, from the cached field widths. A field lying fully
        // inside the contour span is an intentional overlay and reserves nothing. A field outside the contour reserves
        // a band only if it vertically intersects at least one row of this side; otherwise it reserves nothing.
        // A field partly over the contour edge is counted as ambiguous and is reserved only if it intersects a row.
        private function extraBands(owner:Object,widths:Object,left:Boolean,anchor:Number,contour:Number):Array
        {
            var list:Array=left ? widths.fieldsAlly as Array : widths.fieldsEnemy as Array;
            var bands:Array=[], overlays:int=0, conflicts:int=0, independent:int=0, seen:Object={};
            var screenEdge:Number=left ? 0 : Number(owner.width);
            var cLo:Number=left ? anchor : anchor-contour, cHi:Number=left ? anchor+contour : anchor;
            if (list)
            {
                for each (var field:Object in list)
                {
                    var start:Number=(field.bind ? anchor : screenEdge)+(left ? Number(field.x) : -Number(field.x));
                    var align:String=field.align ? String(field.align) : (left ? "left" : "right");
                    if (align=="right") start-=Number(field.w);
                    else if (align=="center") start-=Number(field.w)/2;
                    var lo:Number=start, hi:Number=start+Number(field.w);
                    if (lo>=cLo && hi<=cHi) { ++overlays; continue; }
                    if (!fieldIntersectsRows(owner,left,field)) continue;
                    if (lo<cHi && hi>cLo) ++conflicts;
                    var key:String=lo+"|"+hi;
                    if (seen[key]) continue;
                    seen[key]=true;
                    bands.push({lo:lo,hi:hi});
                    ++independent;
                }
            }
            if (left) { layoutOverlayAlly=overlays; layoutIndependentAlly=independent; layoutConflictAlly=conflicts; }
            else { layoutOverlayEnemy=overlays; layoutIndependentEnemy=independent; layoutConflictEnemy=conflicts; }
            return bands;
        }
        // Vertical test with the same arithmetic as extrafields.draw: top = rowY + y, shifted by valign; height from config.
        private function fieldIntersectsRows(owner:Object,left:Boolean,field:Object):Boolean
        {
            var nicks:Object=owner[left ? "textFieldsAlly" : "textFieldsEnemy"];
            if (!nicks) return false;
            var h:Number=Number(field.h);
            var offset:Number=field.v=="bottom" ? -h : (field.v=="center" ? -h/2 : 0);
            for (var i:int=0;i<nicks.length;++i)
            {
                var nick:DisplayObject=nicks[i] as DisplayObject;
                if (!nick || !state.base(nick,"visible")) continue;
                var rowTop:Number=Number(nick.y), rowBottom:Number=rowTop+Number(nick.height);
                var fieldTop:Number=rowTop+Number(field.y)+offset, fieldBottom:Number=fieldTop+h;
                if (fieldTop<rowBottom && fieldBottom>rowTop) return true;
            }
            return false;
        }
        // Moves a column outward past every band it overlaps. The column's inner edge is the cursor; the band's
        // outermost edge is the one facing outward. Deterministic: bounded by the number of bands.
        private function pushClear(cursor:Number,width:Number,outward:int,bands:Array,gap:Number):Number
        {
            if (width<=0 || bands.length==0) return cursor;
            var guard:int=0, moved:Boolean=true;
            while (moved && guard<=bands.length)
            {
                moved=false; ++guard;
                var colLo:Number=outward<0 ? cursor-width : cursor, colHi:Number=outward<0 ? cursor : cursor+width;
                for each (var band:Object in bands)
                {
                    if (Number(band.hi)>colLo && Number(band.lo)<colHi)
                    {
                        cursor=outward<0 ? Number(band.lo)-gap : Number(band.hi)+gap;
                        moved=true; ++layoutPushCount;
                        break;
                    }
                }
            }
            return cursor;
        }
        private function loadingWidths(owner:Object,payload:Object,screen:String):Object
        {
            var first:TextField=owner["textFieldsAlly"] && owner["textFieldsAlly"].length ? (owner["textFieldsAlly"][0] as TextField) : null;
            var fmt:TextFormat=first ? first.getTextFormat() : null;
            var key:String=(fmt ? fmt.font+"|"+fmt.size : "")+"|"+screen;
            var rows:int=payload.rows.length;
            if (widthCache && cacheOwner===owner && cachePayload===payload && cacheKey===key && cacheRows===rows) return widthCache;
            var nick:Number=0, vehicleActual:Number=0, vehicleEstimate:Number=0, unavailable:int=0, sample:Object=null;
            var fieldsAlly:Array=[], fieldsEnemy:Array=[], seenFields:Object={};
            for each (var row:Object in payload.rows)
            {
                var cfg:Object=row["loading"];
                if (!cfg || !cfg.enabled) continue;
                if (!sample) sample=cfg;
                // Independent extra-field geometry: width from the configured width, or the measured formatted text when
                // no width is configured. Cached with the widths; no per-frame measurement.
                if (cfg.fields)
                {
                    for each (var field:Object in cfg.fields)
                    {
                        if (field.visible===false) continue;
                        var fieldWidth:Number=field.width!==undefined && field.width!==null ? nativestate.number(field.width,0) : measureRaw(field.format,fmt);
                        if (fieldWidth<=0) continue;
                        var entry:Object={x:nativestate.number(field.x), w:fieldWidth, bind:nativestate.flag(field.bindToIcon),
                                          align:field.align ? String(field.align) : "", y:nativestate.number(field.y),
                                          h:Math.max(0,nativestate.number(field.height,25)), v:field.valign ? String(field.valign) : ""};
                        var fieldKey:String=(row.ally ? "A" : "E")+"|"+entry.x+"|"+entry.w+"|"+entry.bind+"|"+entry.align+"|"+entry.y+"|"+entry.h+"|"+entry.v;
                        if (seenFields[fieldKey]) continue;
                        seenFields[fieldKey]=true;
                        (row.ally ? fieldsAlly : fieldsEnemy).push(entry);
                    }
                }
                var nickL:Number=measureRaw(cfg.formatLeftNick,fmt), nickR:Number=measureRaw(cfg.formatRightNick,fmt);
                nick=Math.max(nick,nickL>0 ? nickL+LAYOUT_GUTTER : 0,nickR>0 ? nickR+LAYOUT_GUTTER : 0);
                // Rating statistics render at size 0 until their data arrives. The estimate measures the same
                // configured format with the statistics at their visible size; it is never displayed.
                var vehL:String=cfg.formatLeftVehicle===null || cfg.formatLeftVehicle===undefined ? "" : String(cfg.formatLeftVehicle);
                var vehR:String=cfg.formatRightVehicle===null || cfg.formatRightVehicle===undefined ? "" : String(cfg.formatRightVehicle);
                if (HIDDEN_STATS.test(vehL) || HIDDEN_STATS.test(vehR)) unavailable++;
                vehicleActual=Math.max(vehicleActual,measureRaw(vehL,fmt),measureRaw(vehR,fmt));
                vehicleEstimate=Math.max(vehicleEstimate,measureRaw(sizedStats(vehL),fmt),measureRaw(sizedStats(vehR),fmt));
            }
            // Reset the reservation only when the view, its font or the effective vehicle configuration changes.
            var reserveKey:String=(fmt ? fmt.font+"|"+fmt.size : "")+"|"+configSignature(sample);
            if (reservationOwner!==owner || reservationKey!==reserveKey) { reservedVehicle=0; reservationOwner=owner; reservationKey=reserveKey; }
            var needed:Number=Math.max(vehicleActual,vehicleEstimate);
            if (needed>0) reservedVehicle=Math.max(reservedVehicle,needed+LAYOUT_GUTTER);
            var prestige:Number=sample && sample.removePrestigeLevel ? 0 : Math.max(maxWidthOf(owner,"prestigeLevelsAlly"),maxWidthOf(owner,"prestigeLevelsEnemy"));
            // Disabled class icon releases its column; opacity alone does not.
            var klass:Number=sample && sample.removeVehicleTypeIcon ? 0 : Math.max(maxWidthOf(owner,"vehicleTypeIconsAlly"),maxWidthOf(owner,"vehicleTypeIconsEnemy"));
            // Disabled badges and squads release their columns; visible ones use their occupied width.
            var badgeW:Number=sample && sample.removeRankBadgeIcon ? 0 : Math.max(maxWidthOf(owner,"badgesAlly"),maxWidthOf(owner,"badgesEnemy"));
            var squadW:Number=sample && sample.removeSquadIcon ? 0 : Math.max(maxWidthOf(owner,"squadsAlly"),maxWidthOf(owner,"squadsEnemy"));
            widthCache={nick:nick,vehicle:reservedVehicle,prestige:prestige,klass:klass,badge:badgeW,squad:squadW,sample:sample,
                        fieldsAlly:fieldsAlly,fieldsEnemy:fieldsEnemy};
            cacheOwner=owner; cachePayload=payload; cacheKey=key; cacheRows=rows;
            layoutRevision++; layoutNickW=nick; layoutVehicleW=reservedVehicle; layoutVehicleActual=vehicleActual;
            layoutReservedVehicle=reservedVehicle; layoutPrestigeW=prestige; layoutClassW=klass; layoutRowsUnavailable=unavailable;
            return widthCache;
        }
        private function loadingLimits(owner:Object):Object
        {
            var limits:Object={left:-1e9,right:1e9};
            var display:DisplayObject=owner as DisplayObject;
            if (display && display.stage)
            {
                var a:Point=display.globalToLocal(new Point(0,0));
                var b:Point=display.globalToLocal(new Point(display.stage.stageWidth,0));
                limits.left=Math.min(a.x,b.x)+LAYOUT_MARGIN;
                limits.right=Math.max(a.x,b.x)-LAYOUT_MARGIN;
            }
            layoutLimitLeft=Number(limits.left); layoutLimitRight=Number(limits.right);
            return limits;
        }
        // Places one row's nick and vehicle text. Native widths and offsets follow format(); the vehicle keeps its
        // inner edge and the nick grows outward. Returns the outward shift for the adjacent badge and squad.
        private function placeLoading(owner:Object,i:int,nick:TextField,vehicle:TextField,cfg:Object,side:String,sign:int,widths:Object,geo:Object):void
        {
            var nickText:*=cfg["format"+side+"Nick"], vehicleText:*=cfg["format"+side+"Vehicle"];
            if (nickText===null || nickText===undefined || vehicleText===null || vehicleText===undefined) return;
            var left:Boolean=sign>0, suffix:String=left ? "Ally" : "Enemy";
            // Each text hugs the icon or column it belongs to: vehicle text against the class icon, nick text against
            // the badges. The unused width of the shared column sits between the two text columns.
            extra.drawText(vehicle,String(vehicleText),geo.vehicleLeft,Number(widths.vehicle),nativestate.flag(cfg.vehicleFieldShowBorder),false,left ? "right" : "left");
            extra.drawText(nick,String(nickText),geo.nickLeft,Number(widths.nick),nativestate.flag(cfg.nameFieldShowBorder),false,left ? "left" : "right");
            state.setValue(vehicle,"visible",false);
            state.setValue(nick,"visible",false);
            // Every native column is placed by its occupied bounds from the shared edges, never by its own origin.
            var typeItem:DisplayObject=at(owner,"vehicleTypeIcons"+suffix,i) as DisplayObject;
            var eliteItem:DisplayObject=at(owner,"prestigeLevels"+suffix,i) as DisplayObject;
            var badgeItem:DisplayObject=at(owner,"badges"+suffix,i) as DisplayObject;
            var squadItem:DisplayObject=at(owner,"squads"+suffix,i) as DisplayObject;
            if (typeItem) state.setValue(typeItem,"x",geo.classAnchor-occupiedOffset(typeItem)-(left ? typeItem.width : 0));
            if (eliteItem) state.setValue(eliteItem,"x",geo.prestigeAnchor-occupiedOffset(eliteItem)-(left ? eliteItem.width : 0)+sign*nativestate.number(cfg["prestigeOffsetX"+side]));
            if (badgeItem) state.setValue(badgeItem,"x",geo.badgeAnchor-occupiedOffset(badgeItem)-(left ? badgeItem.width : 0));
            if (squadItem) state.setValue(squadItem,"x",geo.squadAnchor-occupiedOffset(squadItem)-(left ? squadItem.width : 0)+sign*nativestate.number(cfg["squadIconOffsetX"+side]));
            if (geo.overflow>0) layoutOverflow=Math.max(layoutOverflow,Number(geo.overflow));
        }
        // Occupied extent of a row's extra fields against the table. A field fully inside the contour is an intended
        // overlay; any part that reaches the text columns is a collision. Measured only, never reserved.
        private function extraSpan(cfg:Object,left:Boolean,geo:Object,screenEdge:Number):void
        {
            var fields:Array=cfg.fields as Array;
            if (!fields) return;
            var bandLo:Number=Math.min(Number(geo.outerEdge),Number(geo.anchor)), bandHi:Number=Math.max(Number(geo.outerEdge),Number(geo.anchor));
            for each (var field:Object in fields)
            {
                if (field.visible===false) continue;
                var w:Number=Math.max(0,nativestate.number(field.width,350));
                var base:Number=nativestate.flag(field.bindToIcon) ? Number(geo.anchor) : screenEdge;
                var start:Number=base+(left ? nativestate.number(field.x) : -nativestate.number(field.x));
                var align:String=field.align ? String(field.align) : (left ? "left" : "right");
                if (align=="right") start-=w; else if (align=="center") start-=w/2;
                var lo:Number=start, hi:Number=start+w;
                if (lo<bandHi && hi>bandLo) ++layoutExtraCollisions;
                var reach:Number=left ? Number(geo.anchor)-lo : hi-Number(geo.anchor);
                if (reach>layoutExtraSpan) layoutExtraSpan=reach;
            }
        }
        public function draw(owner:Object,payload:Object,screen:String,left:Boolean=true):void
        {
            var tab:Boolean=screen=="tab", suffix:String=left ? "Ally" : "Enemy";
            var nicks:Object=tab ? owner.playerNameCollection : owner["textFields"+suffix];
            var vehicles:Object=tab ? owner.vehicleNameCollection : owner["vehicleFields"+suffix];
            if (!nicks || !vehicles) return;
            var widths:Object=null, limits:Object=null, geo:Object=null;
            if (!tab)
            {
                widths=loadingWidths(owner,payload,screen);
                limits=loadingLimits(owner);
                geo=loadingGeometry(owner,suffix,left ? 1 : -1,widths,limits,LAYOUT_GAP);
                // Overflow fallback: if the normal gutter does not fit the viewport, compact it. Deterministic: the
                // result depends only on the current widths and viewport, so it cannot oscillate.
                var compact:int=0;
                if (geo.valid && Number(geo.overflow)>0)
                {
                    geo=loadingGeometry(owner,suffix,left ? 1 : -1,widths,limits,COMPACT_GAP);
                    compact=1;
                }
                if (left) layoutCompactAlly=compact; else layoutCompactEnemy=compact;
                if (left) layoutOverflow=0;
                layoutExtraCollisions=0; layoutExtraSpan=0;
            }
            var count:int=tab ? ("numRows" in owner ? int(owner.numRows) : nicks.length/2) : nicks.length;
            var rowTop:Number=NaN, rowBottom:Number=NaN, placedRows:int=0;
            for (var i:int=0;i<nicks.length && i<vehicles.length;++i)
            {
                if (tab) left=i<count;
                suffix=left ? "Ally" : "Enemy";
                var side:String=left ? "Left" : "Right", sign:int=left ? 1 : -1;
                var nick:TextField=nicks[i] as TextField, vehicle:TextField=vehicles[i] as TextField;
                if (!nick || !vehicle || !state.base(nick,"visible")) continue;
                var row:Object=rowlookup.find(payload.rows,tab ? i%count : i,left,nick.text);
                if (!row) continue;
                var cfg:Object=row[screen=="tips" ? "loading" : screen];
                if (!cfg || !cfg.enabled) continue;
                ++matched;
                var prestige:Number=tab && cfg.removePrestigeLevel ? 15 : 0;
                if (tab)
                {
                    format(nick,cfg["format"+side+"Nick"],cfg,"name",side,sign,tab,0);
                    format(vehicle,cfg["format"+side+"Vehicle"],cfg,"vehicle",side,sign,tab,sign*prestige);
                }
                else if (geo && geo.valid)
                {
                    placeLoading(owner,i,nick,vehicle,cfg,side,sign,widths,geo);
                    ++placedRows;
                    var rowLo:Number=Math.min(nick.y,vehicle.y), rowHi:Number=Math.max(nick.y+nick.height,vehicle.y+vehicle.height);
                    rowTop=isNaN(rowTop) ? rowLo : Math.min(rowTop,rowLo);
                    rowBottom=isNaN(rowBottom) ? rowHi : Math.max(rowBottom,rowHi);
                    extraSpan(cfg,left,geo,left ? 0 : Number(owner.width));
                }
                else
                {
                    format(nick,cfg["format"+side+"Nick"],cfg,"name",side,sign,tab,0);
                    format(vehicle,cfg["format"+side+"Vehicle"],cfg,"vehicle",side,sign,tab,sign*prestige);
                }
                var frags:TextField=at(owner,"fragsCollection",i) as TextField;
                if (tab && frags) format(frags,cfg["format"+side+"Frags"],cfg,"frags",side,sign,true,0);
                var icon:Object=at(owner,tab ? "vehicleIconCollection" : "vehicleIcons"+suffix,i);
                var tier:Object=at(owner,tab ? "vehicleLevelCollection" : "vehicleLevelIcons"+suffix,i);
                var type:Object=at(owner,tab ? "vehicleTypeCollection" : "vehicleTypeIcons"+suffix,i);
                move(icon,sign*(nativestate.number(cfg["vehicleIconOffsetX"+side])-prestige));
                move(tier,sign*(nativestate.number(cfg["vehicleIconOffsetX"+side])-prestige));
                if (tab) move(type,sign*(nativestate.number(cfg["vehicleIconOffsetX"+side])+prestige));
                if (icon) state.setValue(icon,"alpha",(cfg.darkenNotReadyIcon===false ? 1 : state.base(icon,"alpha"))*nativestate.number(cfg.vehicleIconAlpha,100)/100);
                if (cfg.removeVehicleLevel) state.setValue(tier,"alpha",0);
                if (cfg.removeVehicleTypeIcon) state.setValue(type,"alpha",0);
                var badge:Object=at(owner,tab ? "rankBadgesCollection" : "badges"+suffix,i);
                if (cfg.removeRankBadgeIcon) state.setValue(badge,"alpha",0);
                var elite:Object=at(owner,tab ? "prestigeLevelCollection" : "prestigeLevels"+suffix,i);
                if (tab) move(elite,sign*nativestate.number(cfg["prestigeOffsetX"+side]));
                if (cfg.removePrestigeLevel) state.setValue(elite,"alpha",0);
                for each (var name:String in tab ? ["icoTesterCollection","testerBackCollection"] : ["icoTesters"+suffix,"backTesters"+suffix])
                    if (cfg.removeTesterIcon) state.setValue(at(owner,name,i),"alpha",0);
                var squad:Object=at(owner,tab ? "squadCollection" : "squads"+suffix,i);
                if (tab || !(geo && geo.valid)) move(squad,sign*nativestate.number(cfg["squadIconOffsetX"+side]));
                if (cfg.removeSquadIcon) state.setValue(squad,"alpha",0);
                if (cfg.removePlayerStatusIcon) state.setValue(at(owner,"playerStatusCollection",i),"alpha",0);
                var edge:Number=!tab && geo && geo.valid ? Number(geo.anchor) : (icon ? Number(icon.x)+(left ? 0 : Number(icon.width)) : vehicle.x);
                extra.draw(owner as DisplayObjectContainer,screen+":"+row.id,cfg.fields,left,edge,nick.y,left ? 0 : Number(owner.width));
            }
            if (!tab)
            {
                if (geo && geo.valid && placedRows>0)
                {
                    var headerTop:Number=alignHeader(owner,suffix,left,geo,nicks);
                    updateSubstrate(owner,suffix,left,geo,rowTop,rowBottom,headerTop);
                }
                else hideSubstrate(owner,suffix);
            }
        }
        // Dark substrate: one black Shape per side, behind the table content, sized from the occupied table bounds.
        // Only the lateral extent of the table is covered; the native artwork, map and progress bar are not touched.
        private function substrate(owner:Object,suffix:String,create:Boolean):Shape
        {
            var set:Object=substrates[owner];
            if (!set)
            {
                if (!create) return null;
                set={}; substrates[owner]=set;
            }
            var shape:Shape=set[suffix] as Shape;
            if (!shape && create)
            {
                // A plain Shape is not an InteractiveObject: it receives no mouse input and cannot block tooltips.
                shape=new Shape();
                set[suffix]=shape;
            }
            return shape;
        }
        private function updateSubstrate(owner:Object,suffix:String,left:Boolean,geo:Object,top:Number,bottom:Number,headerTop:Number):void
        {
            var holder:DisplayObject=owner as DisplayObject;
            if (!holder || !holder.parent) return;
            var contour:Number=maxWidthOf(owner,"vehicleIcons"+suffix);
            // Exterior edge covers independent extra fields as well as the table; the header row is included vertically.
            var outer:Number=Number(geo.exteriorEdge);
            var topEdge:Number=isNaN(headerTop) ? top : Math.min(top,headerTop);
            var inner:Number=left ? Number(geo.anchor)+contour : Number(geo.anchor)-contour;
            // Centre gap between the two contour inner edges, from the shared anchors of both sides.
            var centre:Number=(layoutAnchorEnemy-layoutAnchorAlly)-2*contour;
            var innerFade:Number=Math.max(0,Math.min(BG_FADE,centre/2-BG_PAD));
            var outerFade:Number=BG_FADE;
            var lo:Number=Math.min(outer,inner), hi:Number=Math.max(outer,inner);
            var lowFade:Number=outer<=inner ? outerFade : innerFade;
            var highFade:Number=outer<=inner ? innerFade : outerFade;
            var x0:Number=lo-lowFade, x1:Number=hi+highFade;
            var yTop:Number=topEdge-BG_PAD, h:Number=bottom-topEdge+2*BG_PAD;
            var w:Number=Math.max(1,x1-x0);
            // Display-list host: the native table background's parent, with the Shape inserted directly above that
            // background. The Shape then lies above the native background and below every other visible object (the
            // table, team headers, header icons, map). Inside the table container it sat above the headers: that was the
            // beta.13 contrast loss.
            var background:DisplayObject=findHeader(owner,"formBackgroundTable");
            var host:DisplayObjectContainer=background && background.parent ? background.parent as DisplayObjectContainer
                : holder.parent as DisplayObjectContainer;
            if (!host) return;
            var index:int=background && background.parent===host ? host.getChildIndex(background)+1 : host.getChildIndex(holder);
            // Coordinates are converted into the host space; the owner transform is scale 1 in the captured layout.
            var corner:Point=host.globalToLocal(holder.localToGlobal(new Point(x0,yTop)));
            var hx:Number=corner.x, hy:Number=corner.y;
            var key:String=[hx,hy,w,h,BG_ALPHA,outerFade,innerFade].join("|");
            var shape:Shape=substrate(owner,suffix,true);
            if (shape.parent!==host) host.addChildAt(shape,Math.min(index,host.numChildren));
            shape.visible=true;
            if (substrateKey(owner,suffix)!==key)
            {
                // Native ActionScript gradient: 0 -> BG_ALPHA over the outer fade, solid core, BG_ALPHA -> 0 over the inner fade.
                var matrix:Matrix=new Matrix();
                matrix.createGradientBox(w,h,0,hx,hy);
                var lowRatio:Number=(lo-x0)/w*255, highRatio:Number=(hi-x0)/w*255;
                shape.graphics.clear();
                shape.graphics.beginGradientFill("linear",[0x000000,0x000000,0x000000,0x000000],
                    [0,BG_ALPHA,BG_ALPHA,0],[0,Math.round(lowRatio),Math.round(highRatio),255],matrix);
                shape.graphics.drawRect(hx,hy,w,h);
                shape.graphics.endFill();
                setSubstrateKey(owner,suffix,key);
            }
            if (left) { layoutBgAllyX0=x0; layoutBgAllyX1=x1; } else { layoutBgEnemyX0=x0; layoutBgEnemyX1=x1; }
            layoutBgY0=yTop; layoutBgY1=yTop+h;
            layoutBgFade=outerFade;
        }
        private function substrateKey(owner:Object,suffix:String):String
        {
            var set:Object=substrates[owner];
            return set && set[suffix+"Key"] ? String(set[suffix+"Key"]) : "";
        }
        private function setSubstrateKey(owner:Object,suffix:String,key:String):void
        {
            var set:Object=substrates[owner];
            if (set) set[suffix+"Key"]=key;
        }
        // Team headers: the native text fields live outside the row container, so they are found by name from the
        // owner's ancestors (bounded search, cached per owner). Only their x is moved, from base positions.
        private function findHeader(owner:Object,name:String):DisplayObject
        {
            var cache:Object=headers[owner];
            if (!cache) { cache={}; headers[owner]=cache; }
            if (name in cache) return cache[name] as DisplayObject;
            var node:DisplayObject=owner as DisplayObject, found:DisplayObject=null;
            for (var level:int=0; level<4 && node && !found; ++level)
            {
                node=node.parent;
                var container:DisplayObjectContainer=node as DisplayObjectContainer;
                if (container) found=findChildNamed(container,name,2);
            }
            cache[name]=found;
            return found;
        }
        private function findChildNamed(node:DisplayObjectContainer,name:String,depth:int):DisplayObject
        {
            var direct:DisplayObject=node.getChildByName(name);
            if (direct || depth<=0) return direct;
            for (var i:int=0;i<node.numChildren;++i)
            {
                var child:DisplayObjectContainer=node.getChildAt(i) as DisplayObjectContainer;
                if (child)
                {
                    var found:DisplayObject=findChildNamed(child,name,depth-1);
                    if (found) return found;
                }
            }
            return null;
        }
        // Moves the team header so its exterior edge matches the table's exterior content edge. The shift is the
        // difference between the native nick edge and the table edge, both measured in the header's parent space.
        private function alignHeader(owner:Object,suffix:String,left:Boolean,geo:Object,nicks:Object):Number
        {
            var header:DisplayObject=findHeader(owner,left ? "team1Text" : "team2Text");
            var holder:DisplayObject=owner as DisplayObject;
            if (!header || !header.parent || !holder) return NaN;
            var nativeEdge:Number=NaN;
            for (var i:int=0;i<nicks.length;++i)
            {
                var nick:TextField=nicks[i] as TextField;
                if (!nick || !state.base(nick,"visible")) continue;
                var edge:Number=left ? state.base(nick,"x") : state.base(nick,"x")+nick.width;
                if (isNaN(nativeEdge)) nativeEdge=edge;
                else nativeEdge=left ? Math.min(nativeEdge,edge) : Math.max(nativeEdge,edge);
            }
            if (isNaN(nativeEdge)) return NaN;
            var parent:DisplayObject=header.parent;
            var target:Point=parent.globalToLocal(holder.localToGlobal(new Point(Number(geo.exteriorEdge),0)));
            var native:Point=parent.globalToLocal(holder.localToGlobal(new Point(nativeEdge,0)));
            var delta:Number=target.x-native.x;
            // Header text is aligned by its native alignment: left header on the ally side, right header on the enemy side.
            var base:Number=state.base(header,"x");
            state.setValue(header,"x",base+delta);
            // The header's small native icons move with it, by the same parent-space delta, from their base positions.
            var icons:Array=headerIcons(owner,left,header);
            for each (var icon:DisplayObject in icons) state.setValue(icon,"x",state.base(icon,"x")+delta);
            layoutHeaderIcons=icons.length;
            if (left) layoutHeaderDeltaAlly=delta; else layoutHeaderDeltaEnemy=delta;
            var box:*=header.getBounds(holder);
            return Number(box.y);
        }
        // Native header icons, bound by name. The 21:38 diagnostic confirmed the objects: per side, the squad icon sits
        // next to the header text and the tank icon sits in the header row. Only these named children of the header
        // text's parent are ever moved; a missing name is skipped.
        private static const HEADER_ICONS_ALLY:Array=["leftSquad","leftTank"];
        private static const HEADER_ICONS_ENEMY:Array=["rightSquad","rightTank"];
        private function headerIcons(owner:Object,left:Boolean,header:DisplayObject):Array
        {
            var cache:Object=headers[owner];
            if (!cache) { cache={}; headers[owner]=cache; }
            var key:String=left ? "allyIcons" : "enemyIcons";
            if (key in cache) return cache[key] as Array;
            var result:Array=[];
            var parent:DisplayObjectContainer=header.parent as DisplayObjectContainer;
            if (parent)
            {
                for each (var iconName:String in left ? HEADER_ICONS_ALLY : HEADER_ICONS_ENEMY)
                {
                    var icon:DisplayObject=parent.getChildByName(iconName);
                    if (icon) result.push(icon);
                }
            }
            cache[key]=result;
            return result;
        }
        private function hideSubstrate(owner:Object,suffix:String):void
        {
            var shape:Shape=substrate(owner,suffix,false);
            if (shape) shape.visible=false;
        }
        // Removes every substrate. Called when the loading view has no rows (ratings disabled or view closed).
        public function restoreBackground():void
        {
            for (var key:Object in substrates)
            {
                var set:Object=substrates[key];
                for each (var item:Object in set)
                {
                    var shape:Shape=item as Shape;
                    if (shape && shape.parent) shape.parent.removeChild(shape);
                }
            }
            substrates=new Dictionary(true);
            // Drop cached header and icon references so a recreated view never reuses stale display objects.
            headers=new Dictionary(true);
        }
        private function move(target:Object,dx:Number):void
        { if (target) state.setValue(target,"x",state.base(target,"x")+dx); }
        private function format(field:TextField,text:*,cfg:Object,prefix:String,side:String,sign:int,absolute:Boolean,additional:Number):void
        {
            if (text===null || text===undefined) return;
            var width:Number=absolute ? nativestate.number(cfg[prefix+"FieldWidth"+side],field.width) : field.width+nativestate.number(cfg[prefix+"FieldWidthDelta"+side]);
            var shift:Number=sign*nativestate.number(cfg[prefix+"FieldOffsetX"+side])+additional;
            if (prefix=="frags") shift+=(field.width-width)/2;
            else if (prefix=="name" && sign<0 || prefix=="vehicle" && sign>0) shift+=field.width-width;
            extra.drawText(field,String(text),field.x+shift,Math.max(0,width),nativestate.flag(cfg[prefix+"FieldShowBorder"]));
            state.setValue(field,"visible",false);
        }
    }
}
