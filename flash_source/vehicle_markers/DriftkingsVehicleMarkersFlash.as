package
{
    import flash.display.GradientType;
    import flash.geom.Matrix;
    import flash.filters.ColorMatrixFilter;
    import flash.display.Sprite;
    import flash.display.DisplayObjectContainer;
    import flash.text.TextField;
    import flash.text.TextFormat;
    import flash.filters.DropShadowFilter;
    import flash.utils.Dictionary;
    import flash.utils.getTimer;
    import flash.events.Event;

    /** Integrated marker layouts and cached player ratings; native game events remain in control. */
    public class DriftkingsVehicleMarkersFlash extends Sprite
    {
        private static var config:Object;
        private static var records:Dictionary = new Dictionary(true);
        private static var reported:Boolean = false;
        private static var colorBlind:Boolean = false;
        private static var damageRecords:Dictionary = new Dictionary(true);
        private static var animations:Dictionary = new Dictionary(true);
        private static var damageColors:Dictionary = new Dictionary(true);
        private static var bars:Dictionary = new Dictionary(true);
        private static var barAnimations:Dictionary = new Dictionary(true);
        private static var iconOriginals:Dictionary = new Dictionary(true);
        private static var nativeCache:Dictionary = new Dictionary(true);
        private static var statistics:Dictionary = new Dictionary();

        public static function receiveStats(settings:Object):Boolean
        {
            if (!settings || !settings.hasOwnProperty("__vmRatings")) return false;
            statistics = new Dictionary();
            if (!config) return true;
            if (config)
                for each (var row:Object in settings.__vmRatings)
                    statistics[String(row.name)] = row.values;
            for (var marker:Object in records)
            {
                var record:Object = records[marker];
                if (record.model) refreshFields(marker, record, record.model, record.dead);
            }
            return true;
        }

        private static function profile(marker:Object, dead:Boolean):Object
        {
            if (!config || !config.profiles) return config;
            var team:String = String(marker.entityType);
            var state:String = dead ? "dead" : "alive";
            var mode:String = marker.exInfo ? "extended" : "normal";
            return config.profiles[team] ? config.profiles[team][state][mode] : null;
        }

        public static function nativeSettings(original:Object, marker:Object, dead:Boolean):Object
        {
            if (!config || !config.profiles || !original) return original;
            var selected:Object = profile(marker, dead);
            if (!selected) return original;
            var cached:Object = nativeCache[marker];
            if (cached && cached.original === original && cached.profile === selected) return cached.value;
            var result:Object = {};
            for (var name:String in original) result[name] = original[name];
            var prefix:String = marker.exInfo ? "markerAlt" : "markerBase";
            var suffixes:Object = {vehicleName:"VehicleName", playerName:"PlayerName", healthBar:"HpIndicator",
                damage:"Damage", vehicleIcon:"Icon", levelIcon:"Level"};
            for (name in selected.native)
                result[prefix + (name == "hp" ? "Hp" : suffixes[name])] = name == "hp"
                    ? ({percent:0, currentAndMax:1, current:2, hidden:3})[selected.native[name]] : selected.native[name];
            if (selected.enabled && selected.fields != null)
            {
                result[prefix + "Hp"] = 3;
                result[prefix + "VehicleName"] = result[prefix + "PlayerName"] = false;
            }
            if (selected.healthBar.enabled) result[prefix + "HpIndicator"] = false;
            if (selected.icons.enabled && !selected.icons.vehicle.enabled) result[prefix + "Icon"] = false;
            nativeCache[marker] = {original:original, profile:selected, value:result};
            return result;
        }

        public static function configure(settings:Object):void
        {
            config = settings && settings.hasOwnProperty("__vmTest") ? settings.__vmTest : null;
            statistics = new Dictionary();
            trace("[Driftkings.VehicleMarkers] Flash configuration received; custom fields=" + Boolean(config && config.enabled));
        }

        public static function setColorBlind(value:Boolean):void
        {
            colorBlind = value;
        }

        private static function clearFields(marker:Object):void
        {
            var record:Object = records[marker];
            if (!record) return;
            if (record.holder.parent) record.holder.parent.removeChild(record.holder);
            delete records[marker];
        }

        public static function clear(marker:Object):void
        {
            restoreIcons(marker);
            delete nativeCache[marker];
            clearFields(marker);
            clearDamage(marker);
            clearBar(marker);
            delete damageColors[marker];
        }

        public static function clearDamage(marker:Object):void
        {
            var record:Object = damageRecords[marker];
            if (!record) return;
            record.holder.removeEventListener(Event.ENTER_FRAME, animateDamage);
            if (record.holder.parent) record.holder.parent.removeChild(record.holder);
            delete animations[record.holder];
            record.items = [];
            delete damageRecords[marker];
        }

        public static function damageEnabled(marker:Object, health:int):Boolean
        {
            // updateHealth updates HP before the separate destroyed-state event arrives.
            var selected:Object = profile(marker, health <= 0);
            if (!selected) return false;
            if (selected.native && selected.native.damage === false) return true;
            if (!selected.damageText) return false;
            for each (var source:Object in selected.damageText.sources) if (source.enabled) return true;
            return Boolean(selected.damageText.enabled);
        }

        public static function damage(marker:Object, model:Object, newHealth:int, flag:uint, kind:String):void
        {
            try
            {
                var selected:Object = profile(marker, newHealth <= 0);
                if (!selected || !selected.damageText || !model) return;
                var source:String = flag == 2 ? "player" : flag == 1 ? "squad" : "other";
                var options:Object = selected.damageText.sources[source];
                if (!options) return;
                var amount:int = Math.max(0, int(model.currHealth)) - Math.max(0, newHealth);
                if (int(model.maxHealth) <= 0 || amount <= 0) return;
                damageColors[marker] = options.colors[source];
                if (!options.enabled || (selected.native && selected.native.damage === false)) return;
                var record:Object = damageRecords[marker];
                if (!record)
                {
                    var holder:Sprite = new Sprite();
                    holder.mouseEnabled = holder.mouseChildren = false;
                    record = {holder:holder, items:[], marker:marker};
                    DisplayObjectContainer(marker).addChild(holder);
                    damageRecords[marker] = record;
                    animations[holder] = record;
                    holder.addEventListener(Event.ENTER_FRAME, animateDamage);
                }
                var count:int = 0;
                for each (var existing:Object in record.items) if (existing.source == source) count++;
                while (count >= options.maxCount)
                {
                    for (var index:int = 0; index < record.items.length; index++)
                        if (record.items[index].source == source)
                        {
                            record.holder.removeChild(record.items[index].field);
                            record.items.splice(index, 1); count--; break;
                        }
                }
                var field:TextField = makeField(options);
                var color:String = options.colors[source];
                var explosion:Boolean = newHealth < 0 || kind == "explosion";
                var event:Object = {dmg:amount, "c:dmg":color, "dmg-ratio":Math.round(100 * amount / model.maxHealth),
                    "dmg-kind":explosion ? "explosion" : kind, "dmg-source":source};
                var template:String = String(explosion ? options.blowupMessage : options.format);
                var after:Object = {currHealth:Math.max(0, newHealth), maxHealth:model.maxHealth,
                    vType:model.vType, vClass:model.vClass, pName:model.pName, pClan:model.pClan, vLevel:model.vLevel, entityName:model.entityName};
                var damageFormat:TextFormat = field.defaultTextFormat;
                damageFormat.color = options.textFormat && options.textFormat.color != null
                    ? rgb(formatText(String(options.textFormat.color), marker, after, newHealth <= 0, event)) : rgb(color);
                field.defaultTextFormat = damageFormat;
                var opacity:Number = Number(formatText(String(options.alpha), marker, after, newHealth <= 0, event));
                opacity = isFinite(opacity) ? Math.max(0, Math.min(100, opacity)) / 100 : 0;
                field.alpha = opacity;
                field.htmlText = formatText(template, marker, after, newHealth <= 0, event);
                record.holder.addChild(field);
                record.items.push({field:field, start:getTimer(), duration:options.duration * 1000,
                    rise:options.rise, y:options.y, alpha:opacity, source:source});
            }
            catch (error:Error)
            {
                clearDamage(marker);
                trace("[Driftkings.VehicleMarkers] Floating damage error: " + error.message);
            }
        }

        private static function animateDamage(event:Event):void
        {
            var record:Object = animations[event.currentTarget];
            if (!record) return;
            var now:int = getTimer();
            for (var i:int = record.items.length - 1; i >= 0; --i)
            {
                var item:Object = record.items[i];
                var progress:Number = (now - item.start) / item.duration;
                if (progress >= 1)
                {
                    record.holder.removeChild(item.field);
                    record.items.splice(i, 1);
                }
                else
                {
                    item.field.y = item.y - item.rise * progress;
                    item.field.alpha = item.alpha * Math.min(1, (1 - progress) * 2);
                }
            }
            if (!record.items.length) clearDamage(record.marker);
        }

        private static function makeField(options:Object):TextField
        {
            var field:TextField = new TextField();
            field.mouseEnabled = field.selectable = false;
            field.width = options.width; field.height = options.height;
            field.x = options.x; field.y = options.y;
            var style:Object = options.textFormat;
            var textFormat:TextFormat = style ? new TextFormat(style.font, style.size, 0xFFFFFF, style.bold, style.italic)
                                             : new TextFormat("$FieldFont", 13, 0xFFFFFF);
            textFormat.align = options.align;
            field.defaultTextFormat = textFormat;
            field.multiline = true; field.wordWrap = false;
            var shadow:Object = options.shadow;
            if (shadow.enabled)
                field.filters = [new DropShadowFilter(shadow.distance, shadow.angle,
                    uint(String(shadow.color).replace("#", "0x")), shadow.alpha / 100,
                    shadow.blur, shadow.blur, shadow.strength)];
            return field;
        }

        public static function clearTransient(marker:Object):void
        {
            delete damageColors[marker];
            clearDamage(marker);
            clearBar(marker);
        }

        private static function stopBarAnimation(record:Object):void
        {
            record.holder.removeEventListener(Event.ENTER_FRAME, animateBar);
            delete barAnimations[record.holder];
        }

        private static function animateBar(event:Event):void
        {
            var record:Object = barAnimations[event.currentTarget];
            if (!record) return;
            var progress:Number = (getTimer() - record.start) / (record.options.damage.duration * 1000);
            if (progress < 0) return;
            progress = Math.min(1, progress);
            record.trail = record.from + (record.ratio - record.from) * progress;
            paintBar(record);
            if (progress >= 1) stopBarAnimation(record);
        }

        private static function clearBar(marker:Object):void
        {
            var record:Object = bars[marker];
            if (!record) return;
            stopBarAnimation(record);
            if (record.holder.parent) record.holder.parent.removeChild(record.holder);
            delete bars[marker];
        }

        private static function rgb(value:String):uint
        {
            return uint(value.replace("#", "0x"));
        }

        private static function updateBar(marker:Object, model:Object, dead:Boolean, sticky:Boolean):void
        {
            var selected:Object = profile(marker, dead);
            var options:Object = selected ? selected.healthBar : null;
            if (!options || !options.enabled || !model || (dead && !options.showOnDead))
            { clearBar(marker); return; }
            var record:Object = bars[marker];
            if (!record || record.options !== options)
            {
                clearBar(marker);
                var holder:Sprite = new Sprite();
                holder.mouseEnabled = holder.mouseChildren = false;
                holder.x = options.x; holder.y = options.y; holder.alpha = options.alpha / 100;
                var shadow:Object = options.shadow;
                if (shadow.enabled)
                    holder.filters = [new DropShadowFilter(shadow.distance, shadow.angle,
                        rgb(shadow.color), shadow.alpha / 100, shadow.blur, shadow.blur, shadow.strength)];
                DisplayObjectContainer(marker).addChild(holder);
                record = {holder:holder, options:options, ratio:-1, color:"", trailColor:"#FFFFFF", trail:0, from:0, start:0};
                bars[marker] = record;
            }
            record.holder.visible = !sticky;
            var maximum:int = int(model.maxHealth);
            var current:int = Math.max(0, int(model.currHealth));
            var ratio:Number = dead || maximum <= 0 ? 0 : Math.max(0, Math.min(1, current / maximum));
            var fill:String = String(options.color);
            if (fill == "{{c:hp}}") fill = hpColor(current, maximum);
            else if (fill == "{{c:team}}") fill = teamColor(marker, model, dead);
            var gradientColor:String = formatText(String(options.gradient.color), marker, model, dead);
            if (record.ratio == ratio && record.color == fill && record.gradientColor == gradientColor) return;
            if (options.damage.enabled && record.ratio >= 0 && ratio < record.ratio)
            {
                record.trailColor = options.damage.color == "{{c:dmg}}" ? (damageColors[marker] || "#FFFFFF") : options.damage.color;
                record.from = Math.max(record.trail, record.ratio);
                record.trail = record.from;
                record.start = getTimer() + options.damage.delay * 1000;
                barAnimations[record.holder] = record;
                record.holder.addEventListener(Event.ENTER_FRAME, animateBar);
            }
            else if (!options.damage.enabled || record.ratio < 0 || ratio >= record.trail)
            {
                stopBarAnimation(record);
                record.trail = ratio;
            }
            record.gradientColor = gradientColor;
            record.ratio = ratio; record.color = fill;
            paintBar(record);
        }

        private static function paintBar(record:Object):void
        {
            var options:Object = record.options;
            var ratio:Number = record.ratio;
            var fill:String = record.color;
            var border:Number = options.border.width;
            var innerWidth:Number = options.width - 2 * border;
            var innerHeight:Number = options.height - 2 * border;
            var shape:Sprite = record.holder;
            shape.graphics.clear();
            // Draw the border as an outer rectangle, keeping all dimensions inside the configured size.
            if (border > 0)
            {
                shape.graphics.beginFill(rgb(options.border.color), options.border.alpha / 100);
                shape.graphics.drawRect(0, 0, options.width, border);
                shape.graphics.drawRect(0, options.height - border, options.width, border);
                shape.graphics.drawRect(0, border, border, innerHeight);
                shape.graphics.drawRect(options.width - border, border, border, innerHeight);
                shape.graphics.endFill();
            }
            shape.graphics.beginFill(rgb(options.background.color), options.background.alpha / 100);
            shape.graphics.drawRect(border, border, innerWidth, innerHeight);
            shape.graphics.endFill();
            if (options.damage.enabled && record.trail > ratio)
            {
                shape.graphics.beginFill(rgb(record.trailColor), options.damage.alpha / 100);
                shape.graphics.drawRect(border + innerWidth * ratio, border,
                    innerWidth * (record.trail - ratio), innerHeight);
                shape.graphics.endFill();
            }
            if (ratio > 0)
            {
                if (options.gradient.enabled)
                {
                    var matrix:Matrix = new Matrix();
                    matrix.createGradientBox(innerWidth * ratio, innerHeight, options.gradient.angle * Math.PI / 180, border, border);
                    shape.graphics.beginGradientFill(GradientType.LINEAR, [rgb(fill), rgb(record.gradientColor)],
                        [options.fill.alpha / 100, options.fill.alpha / 100], [0, 255], matrix);
                }
                else shape.graphics.beginFill(rgb(fill), options.fill.alpha / 100);
                shape.graphics.drawRect(border, border, innerWidth * ratio, innerHeight);
                shape.graphics.endFill();
            }
        }

        private static function escaped(value:Object):String
        {
            return String(value == null ? "" : value).split("&").join("&amp;")
                .split("<").join("&lt;").split(">").join("&gt;")
                .split('"').join("&quot;").split("'").join("&#39;");
        }

        private static function teamColor(marker:Object, model:Object, dead:Boolean):String
        {
            var teams:Object = colorBlind && config.colors.colorBlind.enabled
                ? config.colors.colorBlind.team : config.colors.team;
            var name:String = String(model.entityName).toLowerCase();
            var group:String = String(marker.entityType);
            if (name.indexOf("squad") >= 0) group = "squad";
            else if (name.indexOf("teamkiller") >= 0) group = "teamKiller";
            if (dead) return teams.hasOwnProperty(group + "Dead") ? teams[group + "Dead"] : teams.dead;
            return teams.hasOwnProperty(group) ? teams[group] : teams.unknown;
        }

        private static function hpColor(hp:int, maxHp:int):String
        {
            if (maxHp <= 0) return config.colors.team.unknown;
            var percent:Number = Math.max(0, Math.min(100, 100 * hp / maxHp));
            for each (var band:Object in config.colors.hp)
                if (percent < Number(band.value)) return String(band.color);
            return String(config.colors.hp[config.colors.hp.length - 1].color);
        }

        private static function token(text:String, values:Object):Object
        {
            text = text.replace(/^\s+|\s+$/g, "");
            if (text == "true") return true;
            if (text == "false") return false;
            if (/^-?\d+(?:\.\d+)?$/.test(text)) return Number(text);
            if (text.length >= 2 && (text.charAt(0) == "'" || text.charAt(0) == '"') && text.charAt(text.length - 1) == text.charAt(0)) return text.substring(1, text.length - 1);
            return values[text];
        }

        private static function truth(value:Object):Boolean
        {
            return value != null && value !== false && value !== 0 && value !== "" && value !== "--" && value !== "false" && value !== "0";
        }

        private static function condition(expression:String, values:Object):Boolean
        {
            for each (var group:String in expression.split("||"))
            {
                var all:Boolean = true;
                for each (var part:String in group.split("&&"))
                {
                    part = part.replace(/^\s+|\s+$/g, "");
                    var negate:Boolean = false;
                    while (part.charAt(0) == "!" && part.substr(0, 2) != "!=") { negate = !negate; part = part.substr(1).replace(/^\s+/, ""); }
                    var match:Object = /^(.*?)\s*(<=|>=|==|!=|<|>)\s*(.*?)$/.exec(part);
                    var result:Boolean;
                    if (match)
                    {
                        var left:Object = token(match[1], values), right:Object = token(match[3], values);
                        if (left == null || right == null) result = false;
                        else if (match[2] == "==") result = left === right;
                        else if (match[2] == "!=") result = left !== right;
                        else if (!isFinite(Number(left)) || !isFinite(Number(right))) result = false;
                        else if (match[2] == "<=") result = Number(left) <= Number(right);
                        else if (match[2] == ">=") result = Number(left) >= Number(right);
                        else if (match[2] == "<") result = Number(left) < Number(right);
                        else result = Number(left) > Number(right);
                    }
                    else result = truth(token(part, values));
                    all = all && (negate ? !result : result);
                }
                if (all) return true;
            }
            return false;
        }

        public static function formatText(template:String, marker:Object, model:Object, dead:Boolean, event:Object = null):String
        {
            var hp:int = Math.max(0, int(model.currHealth));
            var maxHp:int = int(model.maxHealth);
            var values:Object = {vehicle:model.vType, name:model.pName, hp:hp,
                maxHp:maxHp > 0 ? maxHp : "--", hpPercent:maxHp > 0 ? Math.round(100 * hp / maxHp) : "--",
                level:model.vLevel};
            var stats:Object = statistics[String(model.pName)];
            var metrics:Array = ["wn8", "wnx", "eff", "xwn8", "xeff", "wgr", "winrate", "battles", "kb", "r", "xr"];
            for each (var metric:String in metrics)
            {
                values[metric] = stats ? stats[metric] : null;
                values["c:" + metric] = stats && stats["c:" + metric] ? stats["c:" + metric] : config.colors.team.unknown;
            }
            values["xvm-stat"] = Boolean(stats && stats["xvm-stat"]);
            values["a:r"] = values["xvm-stat"] ? 100 : 0;
            for each (var keyName:String in ["stock-turret", "turret-vulnerability", "distance", "dist", "ally", "enemy", "player", "squad", "anonym"])
                values[keyName] = stats ? stats[keyName] : null;
            var vulnerability:String = String(values["turret-vulnerability"]);
            values.turret = vulnerability == "high" ? config.turretMarkers.highVulnerability :
                vulnerability == "low" ? config.turretMarkers.lowVulnerability : vulnerability == "unknown" ? config.turretMarkers.unknown : "";
            values.alive = !dead; values.dead = dead;
            values.ally = String(marker.entityType) == "ally";
            values.enemy = String(marker.entityType) == "enemy";
            values["vtype"] = ({lightTank:"LT", mediumTank:"MT", heavyTank:"HT", "AT-SPG":"TD", SPG:"SPG"})[model.vClass];
            values.blownUp = values["l10n:blownUp"] = config.blownUp || "Ammo rack";
            if (event) for (var eventKey:String in event) values[eventKey] = event[eventKey];
            values["nick"] = model.pName;
            values["clan"] = model.pClan ? "[" + model.pClan + "]" : "";
            values["hp-max"] = values.maxHp; values["hp-ratio"] = values.hpPercent;
            values["c:team"] = teamColor(marker, model, dead);
            values["c:system"] = values["c:team"];
            values["c:hp"] = hpColor(hp, maxHp);
            for (var iteration:int = 0; iteration < 12 && template.indexOf("{{") >= 0; iteration++)
            {
                var previous:String = template;
                template = template.replace(/\{\{([^{}]*)\}\}/g, function(...args):String {
                    var expression:String = String(args[1]);
                    var question:int = expression.indexOf("?");
                    var pipe:int = expression.indexOf("|");
                    if (question >= 0)
                    {
                        var branches:Array = expression.substr(question + 1).split("|");
                        return condition(expression.substring(0, question), values) ? branches[0] : (branches.length > 1 ? branches[1] : "");
                    }
                    var fallback:String = pipe >= 0 ? expression.substr(pipe + 1) : "--";
                    var body:String = pipe >= 0 ? expression.substring(0, pipe) : expression;
                    var percent:int = body.indexOf("%");
                    var key:String = percent >= 0 ? body.substring(0, percent) : body;
                    var value:Object = values[key];
                    if (value == null) return fallback;
                    if (percent >= 0)
                    {
                        var spec:String = body.substr(percent + 1);
                        if (spec == "d") value = String(Math.round(Number(value)));
                        else if (/^0?\.[0-3]f$/.test(spec)) value = Number(value).toFixed(int(spec.charAt(spec.length - 2)));
                    }
                    return escaped(value);
                });
                if (previous == template) break;
            }
            return template;
        }

        private static function refreshFields(marker:Object, record:Object, model:Object, dead:Boolean):void
        {
            for each (var item:Object in record.fields)
            {
                var html:String = formatText(item.options.format, marker, model, dead);
                var alpha:Number = Number(formatText(String(item.options.alpha), marker, model, dead));
                item.field.alpha = isFinite(alpha) ? Math.max(0, Math.min(100, alpha)) / 100 : 0;
                var style:Object = item.options.textFormat;
                var color:String = style && style.color != null ? formatText(String(style.color), marker, model, dead) : teamColor(marker, model, dead);
                if (item.last !== html || item.color !== color)
                {
                    var textFormat:TextFormat = item.field.defaultTextFormat;
                    textFormat.color = rgb(color);
                    item.field.defaultTextFormat = textFormat;
                    item.field.htmlText = html;
                    item.last = html; item.color = color;
                }
            }
        }

        private static function applyIcon(icon:Object, options:Object, dead:Boolean):void
        {
            if (!icon || !options) return;
            if (!iconOriginals[icon]) iconOriginals[icon] = {x:icon.x, y:icon.y, scaleX:icon.scaleX, scaleY:icon.scaleY, alpha:icon.alpha};
            // Absolute values avoid accumulating scale or position on repeated native updates.
            if (options.x != null) icon.x = Number(options.x);
            if (options.y != null) icon.y = Number(options.y);
            icon.scaleX = icon.scaleY = Number(options.scale);
            icon.alpha = options.enabled ? Number(options.alpha) / 100 * (dead ? Number(options.deadAlpha) / 100 : 1) : 0;
        }

        private static function applyIndicator(icon:Object, options:Object, dead:Boolean):void
        {
            if (!icon || !options) return;
            if (!iconOriginals[icon]) iconOriginals[icon] = {x:icon.x, y:icon.y, scaleX:icon.scaleX, scaleY:icon.scaleY, filters:icon.filters};
            var original:Object = iconOriginals[icon];
            if (options.x != null) icon.x = Number(options.x);
            if (options.y != null) icon.y = Number(options.y);
            icon.scaleX = original.scaleX * options.scale; icon.scaleY = original.scaleY * options.scale;
            var alpha:Number = options.enabled ? options.alpha / 100 * (dead ? options.deadAlpha / 100 : 1) : 0;
            var filters:Array = original.filters.concat();
            filters.push(new ColorMatrixFilter([1,0,0,0,0, 0,1,0,0,0, 0,0,1,0,0, 0,0,0,alpha,0]));
            icon.filters = filters;
        }

        private static function indicators():Object
        {
            return {actionMarker:"actionMarker", hoverMarker:"vehicleMarkerHoverMC", vehicleStatusMarker:"statusContainer",
                damageIndicator:"criticalHit", damageIndicatorText:"criticalHitLabel", hitExplosion:"hitExplosion"};
        }

        private static function restoreIcon(icon:Object):void
        {
            if (!icon || !iconOriginals[icon]) return;
            var original:Object = iconOriginals[icon];
            for (var key:String in original) icon[key] = original[key];
            delete iconOriginals[icon];
        }

        public static function restoreIcons(marker:Object):void
        {
            if (marker.marker) restoreIcon(marker.marker.vehicleTypeIcon);
            restoreIcon(marker.levelIcon);
            restoreIcon(marker.vehicleIcon);
            var names:Object = indicators();
            for (var key:String in names) restoreIcon(marker[names[key]]);
        }

        private static function updateIcons(marker:Object, dead:Boolean):void
        {
            var selected:Object = profile(marker, dead);
            var options:Object = selected ? selected.icons : null;
            if (!options || !options.enabled) return;
            var names:Object = indicators();
            for (var key:String in names) applyIndicator(marker[names[key]], options[key], dead);
            // Reacquire the timeline child after native state changes; never retain or reparent it.
            if (marker.marker && marker.marker.vehicleTypeIcon)
                applyIcon(marker.marker.vehicleTypeIcon, options["class"], dead);
            if (marker.levelIcon) applyIcon(marker.levelIcon, options.level, dead);
            if (marker.vehicleIcon && options.vehicle) applyIcon(marker.vehicleIcon, options.vehicle, dead);
        }

        public static function render(marker:Object, model:Object, dead:Boolean, sticky:Boolean):void
        {
            try
            {
                if (damageRecords[marker]) damageRecords[marker].holder.visible = !sticky;
                updateIcons(marker, dead);
                updateBar(marker, model, dead, sticky);
                update(marker, model, dead, sticky);
            }
            catch (error:Error)
            {
                clearFields(marker);
                clearBar(marker);
                if (!reported) { trace("[Driftkings.VehicleMarkers] Flash fields error: " + error.message); reported = true; }
            }
        }

        private static function update(marker:Object, model:Object, dead:Boolean, sticky:Boolean):void
        {
            var selected:Object = profile(marker, dead);
            if (!selected || !selected.enabled || !model) { clearFields(marker); return; }
            var group:String = String(marker.entityType);
            var mode:String = marker.exInfo ? "extended" : "normal";
            var fields:Array = selected.fields as Array;
            if (!fields) { clearFields(marker); return; }
            var selection:String = group + "/" + (dead ? "dead" : "alive") + "/" + mode;
            var record:Object = records[marker];
            if (!record || record.selection != selection || record.config !== config)
            {
                clearFields(marker);
                var holder:Sprite = new Sprite();
                holder.mouseEnabled = holder.mouseChildren = false;
                record = {holder:holder, fields:[], selection:selection, config:config};
                for each (var options:Object in fields)
                {
                    if (!options.enabled) continue;
                    var field:TextField = makeField(options);
                    holder.addChild(field);
                    record.fields.push({field:field, options:options, last:null});
                }
                DisplayObjectContainer(marker).addChild(holder);
                records[marker] = record;
            }
            record.holder.visible = !sticky;
            record.model = model; record.dead = dead;
            refreshFields(marker, record, model, dead);
        }
    }
}
