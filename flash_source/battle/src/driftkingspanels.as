package {
import flash.display.MovieClip;

// Code-only library loaded before the battle page while team panels are enabled. Its classes
// carry the names of the client's players panel linkage classes, so the native row symbols bind
// to them; the client's own SWF and graphics are never replaced.
public class driftkingspanels extends MovieClip {
    private static const CLASSES:Array = [PlayersPanelListItemLeftUI, PlayersPanelListItemRightUI,
        PlayerPanelListLeftUI, PlayerPanelListRightUI];

    public function driftkingspanels() {
        super();
    }
}
}
