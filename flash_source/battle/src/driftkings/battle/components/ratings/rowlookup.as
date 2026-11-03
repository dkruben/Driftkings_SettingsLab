package driftkings.battle.components.ratings
{
    public class rowlookup
    {
        // Panels and tables look rows up for every native holder at 10 Hz. Scanning every
        // row and normalising every alias each time cost ~5 ms per frame in a 15 vs 15
        // battle, so the index is built once per payload; results match the plain scan.
        private static const AMBIGUOUS:Object={};
        private static var indexedRows:Array=null;
        private static var byAlias:Object=null;
        private static var byIndex:Object=null;
        private static var byID:Object=null;
        private static var normalizedNicks:Object=null;

        public static function find(rows:Array,index:int,left:Boolean,nick:String):Object
        {
            if (rows!==indexedRows) build(rows);
            var side:String=left ? "L" : "R";
            // Prefixed keys: a nickname such as "toString" must not read Object's prototype.
            var normalized:String=normalizedNicks["n"+nick];
            if (normalized===null || normalized===undefined) normalized=normalizedNicks["n"+nick]=nick.replace(/\s/g,"");
            var found:Object=byAlias[side+normalized];
            // Two rows sharing a name on one side: neither is trusted, as before.
            if (found===AMBIGUOUS) return null;
            return found || byIndex[side+index] || null;
        }

        // Rows tagged by driftkingspanels.swf know their vehicle; a row of the other team is no match.
        public static function byVehicle(rows:Array,vehicleID:Number,left:Boolean):Object
        {
            if (isNaN(vehicleID)) return null;
            if (rows!==indexedRows) build(rows);
            var row:Object=byID["v"+vehicleID];
            return row && Boolean(row.ally)==left ? row : null;
        }

        private static function build(rows:Array):void
        {
            indexedRows=rows; byAlias={}; byIndex={}; byID={}; normalizedNicks={};
            for each (var row:Object in rows)
            {
                byID["v"+row.id]=row;
                var side:String=row.ally ? "L" : "R";
                // The last row with this index wins, as in the plain scan.
                byIndex[side+row.index]=row;
                var aliases:Array=row.aliases || [row.name,row.nick];
                var seen:Object={};
                for each (var alias:String in aliases)
                {
                    if (!alias) continue;
                    var key:String=side+alias.replace(/\s/g,"");
                    if (seen[key]) continue;
                    seen[key]=true;
                    var current:Object=byAlias[key];
                    byAlias[key]=current && current!==row ? AMBIGUOUS : row;
                }
            }
        }
    }
}
