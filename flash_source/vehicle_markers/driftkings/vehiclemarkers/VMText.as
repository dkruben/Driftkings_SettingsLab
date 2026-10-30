package driftkings.vehiclemarkers
{
    import flash.display.DisplayObject;
    import flash.display.DisplayObjectContainer;
    import flash.display.GradientType;
    import flash.display.Sprite;
    import flash.events.Event;
    import flash.filters.ColorMatrixFilter;
    import flash.filters.DropShadowFilter;
    import flash.geom.ColorTransform;
    import flash.geom.Matrix;
    import flash.text.TextField;
    import flash.text.TextFormat;
    import flash.utils.Dictionary;
    import flash.utils.getTimer;

    /** Bounded marker macro language and team/HP colours; mirrors expressions.py and the editor model. */
    public class VMText
    {
        public static function escaped(value:Object):String
        {
            return String(value == null ? "" : value).split("&").join("&amp;")
                .split("<").join("&lt;").split(">").join("&gt;")
                .split('"').join("&quot;").split("'").join("&#39;");
        }

        public static function teamColor(marker:Object, model:Object, dead:Boolean):String
        {
            var teams:Object = VMState.colorBlind && VMState.config.colors.colorBlind.enabled
                ? VMState.config.colors.colorBlind.team : VMState.config.colors.team;
            var name:String = String(model.entityName).toLowerCase();
            var group:String = String(marker.entityType);
            if (name.indexOf("squad") >= 0) group = "squad";
            else if (name.indexOf("teamkiller") >= 0) group = "teamKiller";
            if (dead) return teams.hasOwnProperty(group + "Dead") ? teams[group + "Dead"] : teams.dead;
            return teams.hasOwnProperty(group) ? teams[group] : teams.unknown;
        }

        public static function hpColor(hp:int, maxHp:int):String
        {
            if (maxHp <= 0) return VMState.config.colors.team.unknown;
            var percent:Number = Math.max(0, Math.min(100, 100 * hp / maxHp));
            for each (var band:Object in VMState.config.colors.hp)
                if (percent < Number(band.value)) return String(band.color);
            return String(VMState.config.colors.hp[VMState.config.colors.hp.length - 1].color);
        }

        public static function token(text:String, values:Object):Object
        {
            text = text.replace(/^\s+|\s+$/g, "");
            if (text == "true") return true;
            if (text == "false") return false;
            if (/^-?\d+(?:\.\d+)?$/.test(text)) return Number(text);
            if (text.length >= 2 && (text.charAt(0) == "'" || text.charAt(0) == '"') && text.charAt(text.length - 1) == text.charAt(0)) return text.substring(1, text.length - 1);
            return values[text];
        }

        public static function truth(value:Object):Boolean
        {
            return value != null && value !== false && value !== 0 && value !== "" && value !== "--" && value !== "false" && value !== "0";
        }

        public static function condition(expression:String, values:Object):Boolean
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
            var stats:Object = VMState.statistics[String(model.pName)];
            var metrics:Array = ["wn8", "wnx", "eff", "xwn8", "xeff", "wgr", "winrate", "battles", "kb", "r", "xr"];
            for each (var metric:String in metrics)
            {
                values[metric] = stats ? stats[metric] : null;
                values["c:" + metric] = stats && stats["c:" + metric] ? stats["c:" + metric] : VMState.config.colors.team.unknown;
            }
            values["stat-available"] = Boolean(stats && stats["stat-available"]);
            values["a:r"] = values["stat-available"] ? 100 : 0;
            for each (var keyName:String in ["stock-turret", "turret-vulnerability", "distance", "dist", "ally", "enemy", "player", "squad", "anonym", "battletype", "position"])
                values[keyName] = stats ? stats[keyName] : null;
            var vulnerability:String = String(values["turret-vulnerability"]);
            values.turret = vulnerability == "high" ? VMState.config.turretMarkers.highVulnerability :
                vulnerability == "low" ? VMState.config.turretMarkers.lowVulnerability : vulnerability == "unknown" ? VMState.config.turretMarkers.unknown : "";
            values.alive = !dead; values.dead = dead;
            values.ally = String(marker.entityType) == "ally";
            values.enemy = String(marker.entityType) == "enemy";
            values["vtype"] = ({lightTank:"LT", mediumTank:"MT", heavyTank:"HT", "AT-SPG":"TD", SPG:"SPG"})[model.vClass];
            values.blownUp = values["i18n:blownUp"] = values["l10n:blownUp"] = VMState.config.blownUp || "Ammo rack";
            if (event) for (var eventKey:String in event) values[eventKey] = event[eventKey];
            values["nick"] = model.pName;
            values["clan"] = model.pClan ? "[" + model.pClan + "]" : "";
            values["hp-max"] = values.maxHp; values["hp-ratio"] = values.hpPercent;
            values["c:team"] = teamColor(marker, model, dead);
            values["c:system"] = values["c:team"];
            values["c:hp"] = hpColor(hp, maxHp);
            // Scaleform does not call String.replace callbacks (it inserts the function's text),
            // so the innermost macro is resolved one at a time, as the regex pass did.
            var scanned:int = 0;
            for (var steps:int = 0; steps < 512; steps++)
            {
                var close:int = template.indexOf("}}", scanned);
                if (close < 0) break;
                var open:int = template.lastIndexOf("{{", close);
                var inner:String = template.substring(open + 2, close);
                if (open < 0 || inner.indexOf("{") >= 0 || inner.indexOf("}") >= 0)
                {
                    // Not a macro: braces inside the expression, as the regex excluded.
                    scanned = close + 2;
                    continue;
                }
                var resolved:String = macro(inner, values);
                template = template.substring(0, open) + resolved + template.substr(close + 2);
                scanned = open;
            }
            return template;
        }

        private static function macro(expression:String, values:Object):String
        {
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
        }
    }
}
