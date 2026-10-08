package driftkings.battle.components.ratings
{
    public class RowLookup
    {
        public static function find(rows:Array,index:int,left:Boolean,nick:String):Object
        {
            var found:Object=null, ordered:Object=null;
            var normalized:String=nick.replace(/\s/g,"");
            for each (var row:Object in rows)
            {
                if (Boolean(row.ally)!=left) continue;
                if (row.index==index) ordered=row;
                var aliases:Array=row.aliases || [row.name,row.nick];
                var matches:Boolean=false;
                for each (var alias:String in aliases)
                    if (alias && alias.replace(/\s/g,"")==normalized) { matches=true; break; }
                if (matches) { if (found) return null; found=row; }
            }
            return found || ordered;
        }
    }
}
