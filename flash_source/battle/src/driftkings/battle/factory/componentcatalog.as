// Generated from driftkings/interface_catalog.py; regenerate with generate_ui_catalog.py --write.
package driftkings.battle.factory
{
    import driftkings.battle.components.armor_calculator.armorcalculatorui;
    import driftkings.battle.components.debug_panel.debugpanelui;
    import driftkings.battle.components.dispersion_timer.dispersiontimerui;
    import driftkings.battle.components.distance_marker.distancemarkerui;
    import driftkings.battle.components.flight_timer.flighttimerui;
    import driftkings.battle.components.minimap.minimapenhancementsui;
    import driftkings.battle.components.overlay.overlayui;
    import driftkings.battle.components.ratings.ratingscreens;
    import driftkings.battle.components.sixth_sense.sixthsenseui;

    public class componentcatalog
    {
        public static function classes(surface:String):Object
        {
        if (surface == "battle") return {
                ArmorCalculatorView:armorcalculatorui,
                DispersionTimerView:dispersiontimerui,
                DistanceMarkerView:distancemarkerui,
                DriftkingsDebugPanel:debugpanelui,
                DriftkingsOverlay:overlayui,
                DriftkingsRatingScreens:ratingscreens,
                FlightTimerView:flighttimerui,
                MinimapEnhancementsView:minimapenhancementsui,
                SixthSenseView:sixthsenseui
            };
        if (surface == "ratings") return {
                DriftkingsRatingScreens:ratingscreens
            };
            return {};
        }
    }
}
