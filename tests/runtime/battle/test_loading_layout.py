# -*- coding: utf-8 -*-
"""Battle loading table layout: static contracts on the ActionScript source plus arithmetic models.

The Flash runtime cannot run here. The static tests pin the source contracts (TAB/frontline isolation, shared anchors,
state-tracked writes, rating reservation, diagnostic wiring). The model tests replay the column arithmetic of
``tablerenderer.as`` with plain numbers; they check the arithmetic only. Visual validation is still required in game.
"""
import os
import re

from support import ROOT, RuntimeTest

RATINGS = os.path.join(ROOT, 'flash_source', 'battle', 'src', 'driftkings', 'battle', 'components', 'ratings')
TABLES = os.path.join(RATINGS, 'tablerenderer.as')
SCREENS = os.path.join(RATINGS, 'ratingscreens.as')
EXTRA = os.path.join(RATINGS, 'extrafields.as')

GAP = 4.0


def column_geometry(anchor, prestige, klass, vehicle, nick):
    """Model of loadingGeometry() for the ally side (outer edge = left). Returns each column's edges."""
    # Same cursor walk as tablerenderer.loadingGeometry: a column takes its width plus one gap only when present.
    cursor = anchor - GAP
    prestige_right = cursor
    if prestige > 0:
        cursor -= prestige + GAP
    class_right = cursor
    if klass > 0:
        cursor -= klass + GAP
    vehicle_right = cursor
    vehicle_left = vehicle_right - vehicle
    cursor = vehicle_left - GAP
    nick_right = cursor
    nick_left = nick_right - nick
    return dict(prestige=(prestige_right - prestige, prestige_right), klass=(class_right - klass, class_right),
                vehicle=(vehicle_left, vehicle_right), nick=(nick_left, nick_right))


def mirror(geometry, centre):
    """Mirror a set of left-side spans around a centre line (enemy side)."""
    return {name: (2 * centre - right, 2 * centre - left) for name, (left, right) in geometry.items()}


def reserve(previous, actual, estimate, gutter=6.0):
    """Model of the vehicle reservation: never below the estimate, never shrinking within a view."""
    needed = max(actual, estimate)
    return max(previous, needed + gutter) if needed > 0 else previous


class LoadingLayoutStaticTests(RuntimeTest):
    def read(self, path):
        with open(path, 'rb') as stream:
            return stream.read().decode('utf-8').replace('\r\n', '\n')

    def test_loading_path_is_isolated_from_tab(self):
        text = self.read(TABLES)
        self.assertIn('if (!tab)\n            {\n                widths=loadingWidths(owner,payload,screen);', text)
        self.assertIn('if (tab)\n                {\n                    format(nick,', text)
        self.assertIn('placeLoading(owner,i,nick,vehicle,cfg,side,sign,widths,geo);', text)
        self.assertIn('if (tab) move(type,', text)
        self.assertIn('if (tab) move(elite,', text)
        self.assertIn('var edge:Number=!tab && geo && geo.valid ? Number(geo.anchor)', text)
        self.assertIn('if (tab || !(geo && geo.valid)) move(squad,sign*nativestate.number(cfg["squadIconOffsetX"+side]));', text)
        self.assertNotIn('groupShift', text)

    def test_shared_anchors_are_computed_from_native_bases_not_from_moved_positions(self):
        text = self.read(TABLES)
        body = text[text.index('private function loadingAnchor'):text.index('private function loadingGeometry')]
        self.assertIn('state.base(icon,"x")+shift', body)
        self.assertNotIn('icon.x', body)

    def test_placement_writes_go_through_state_only(self):
        text = self.read(TABLES)
        for name in ('placeLoading', 'loadingGeometry', 'loadingAnchor', 'loadingWidths', 'loadingLimits', 'measureRaw'):
            body = text[text.index('private function ' + name):]
            body = body[:body.index('\n        }\n') + 10]
            self.assertIsNone(re.search(r'\b(vehicle|nick|field|target|type|elite)\.(x|y|width|visible|alpha)\s*=[^=]', body), name)

    def test_reservation_is_reset_only_on_view_font_or_configuration_change(self):
        text = self.read(TABLES)
        body = text[text.index('private function loadingWidths'):text.index('private function loadingLimits')]
        self.assertIn('var reserveKey:String=', body)
        self.assertIn('if (reservationOwner!==owner || reservationKey!==reserveKey) { reservedVehicle=0;', body)
        self.assertIn('reservedVehicle=Math.max(reservedVehicle,needed+LAYOUT_GUTTER);', body)
        self.assertIn('configSignature(sample)', body)

    def test_estimate_measures_the_configured_format_with_statistics_at_visible_size_only(self):
        text = self.read(TABLES)
        self.assertIn("return html.replace(/size='0'/g,\"size='13'\").replace(/size=\"0\"/g,'size=\"13\"');", text)
        self.assertIn('vehicleEstimate=Math.max(vehicleEstimate,measureRaw(sizedStats(vehL),fmt),measureRaw(sizedStats(vehR),fmt));', text)

    def test_text_alignment_hugs_the_neighbouring_column(self):
        text = self.read(TABLES)
        start = text.index('private function placeLoading')
        body = text[start:text.index('public function draw(', start)]
        self.assertIn('left ? "left" : "right"', body)
        self.assertIn('left ? "right" : "left"', body)

    def test_extra_fields_use_the_shared_anchor_and_the_renderer_is_unchanged_otherwise(self):
        text = self.read(TABLES)
        self.assertIn('extra.draw(owner as DisplayObjectContainer,screen+":"+row.id,cfg.fields,left,edge,nick.y', text)
        extra = self.read(EXTRA)
        self.assertIn('fit:Boolean=false,align:String=null', extra)

    def test_columns_are_placed_by_occupied_bounds_not_by_origin(self):
        text = self.read(TABLES)
        start = text.index('private function placeLoading')
        body = text[start:text.index('public function draw(', start)]
        self.assertIn('geo.prestigeAnchor-occupiedOffset(eliteItem)-(left ? eliteItem.width : 0)', body)
        self.assertIn('geo.classAnchor-occupiedOffset(typeItem)-(left ? typeItem.width : 0)', body)

    def test_contour_outer_edge_uses_occupied_bounds_for_mirrored_enemy_contours(self):
        text = self.read(TABLES)
        body = text[text.index('private function loadingAnchor'):text.index('private function loadingGeometry')]
        self.assertIn('var iconLeft:Number=state.base(icon,"x")+shift+occupiedOffset(icon);', body)
        self.assertIn('var outer:Number=sign>0 ? iconLeft : iconLeft+icon.width;', body)

    def test_geometry_uses_one_inward_cursor_and_releases_disabled_columns(self):
        text = self.read(TABLES)
        body = text[text.index('private function loadingGeometry'):text.index('private function loadingWidths')]
        self.assertIn('var cursor:Number=anchor-sign*gap;', body)
        self.assertIn('if (prestige>0) cursor+=outward*(prestige+gap);', body)
        self.assertIn('if (klass>0) cursor+=outward*(klass+gap);', body)
        self.assertNotIn('prestigeAnchor-prestige', body)
        widths = text[text.index('private function loadingWidths'):text.index('private function loadingLimits')]
        self.assertIn('sample && sample.removeVehicleTypeIcon ? 0 :', widths)

    def test_vehicle_text_hugs_the_class_icon_and_nick_text_hugs_the_badges(self):
        text = self.read(TABLES)
        start = text.index('private function placeLoading')
        body = text[start:text.index('private function extraSpan', start)]
        self.assertIn('nativestate.flag(cfg.vehicleFieldShowBorder),false,left ? "right" : "left"', body)
        self.assertIn('nativestate.flag(cfg.nameFieldShowBorder),false,left ? "left" : "right"', body)

    def test_badges_and_squads_are_placed_from_shared_columns_by_occupied_bounds(self):
        text = self.read(TABLES)
        start = text.index('private function placeLoading')
        body = text[start:text.index('private function extraSpan', start)]
        self.assertIn('geo.badgeAnchor-occupiedOffset(badgeItem)-(left ? badgeItem.width : 0)', body)
        self.assertIn('geo.squadAnchor-occupiedOffset(squadItem)-(left ? squadItem.width : 0)', body)
        geometry = text[text.index('private function loadingGeometry'):text.index('private function loadingWidths')]
        self.assertIn('cursor=geo.nickEdge+outward*gap;', geometry)
        self.assertIn('geo.badgeAnchor=cursor;', geometry)
        self.assertIn('cursor+=outward*(badge>0 ? badge+gap : 0);', geometry)
        self.assertIn('geo.squadAnchor=cursor;', geometry)

    def test_disabled_badges_and_squads_release_their_columns(self):
        text = self.read(TABLES)
        widths = text[text.index('private function loadingWidths'):text.index('private function loadingLimits')]
        self.assertIn('sample && sample.removeRankBadgeIcon ? 0 :', widths)
        self.assertIn('sample && sample.removeSquadIcon ? 0 :', widths)

    def test_substrate_is_one_black_shape_per_side_behind_the_table_and_mouse_transparent(self):
        text = self.read(TABLES)
        self.assertIn('private static const BG_ALPHA:Number=0.65;', text)
        self.assertNotIn('shape.mouseEnabled', text)
        self.assertIn('new Shape();', text)
        self.assertNotIn('holder.addChildAt(shape,0);', text)
        self.assertIn('shape.graphics.beginGradientFill("linear"', text)
        self.assertIn('matrix.createGradientBox(w,h,0,hx,hy);', text)
        body = text[text.index('private function updateSubstrate'):text.index('private function hideSubstrate')]
        self.assertNotIn('stage', body)
        self.assertNotIn('ENTER_FRAME', text)

    def test_background_is_restored_when_the_loading_view_has_no_rows(self):
        self.assertIn('tables.restoreBackground();', self.read(SCREENS))
        text = self.read(TABLES)
        start = text.index('public function restoreBackground')
        body = text[start:start + 500]
        self.assertIn('shape.parent.removeChild(shape)', body)
        self.assertIn('substrates=new Dictionary(true);', body)

    def test_extra_fields_are_measured_but_never_reserved(self):
        text = self.read(TABLES)
        start = text.index('private function extraSpan')
        body = text[start:text.index('public function draw(', start)]
        self.assertIn('++layoutExtraCollisions', body)
        # Measurement only: the span must not feed back into any column width or anchor.
        self.assertNotIn('reservedVehicle', body)
        self.assertNotIn('state.setValue', body)
        widths = text[text.index('private function loadingWidths'):text.index('private function loadingLimits')]
        self.assertNotIn('extraSpan', widths)

    def test_background_gradient_is_mirrored_by_construction(self):
        text = self.read(TABLES)
        body = text[text.index('private function updateSubstrate'):text.index('private function substrateKey')]
        # The fade side is chosen from which edge is the outer one, so both sides use the same two-sided construction.
        self.assertIn('var lowFade:Number=outer<=inner ? outerFade : innerFade;', body)
        self.assertIn('var highFade:Number=outer<=inner ? innerFade : outerFade;', body)
        self.assertIn('[0,BG_ALPHA,BG_ALPHA,0]', body)
        self.assertIn('var centre:Number=(layoutAnchorEnemy-layoutAnchorAlly)-2*contour;', body)

    def test_team_headers_are_found_by_bounded_search_and_moved_from_base_positions_only(self):
        text = self.read(TABLES)
        self.assertIn('for (var level:int=0; level<4 && node && !found; ++level)', text)
        start = text.index('private function alignHeader')
        body = text[start:text.index('\n        }', start)]
        self.assertIn('state.setValue(header,"x",base+delta);', body)
        self.assertIn('var base:Number=state.base(header,"x");', body)
        self.assertNotIn('header.x', body)

    def test_compact_gutter_fallback_only_runs_on_overflow_and_is_deterministic(self):
        text = self.read(TABLES)
        self.assertIn('if (geo.valid && Number(geo.overflow)>0)', text)
        self.assertIn('geo=loadingGeometry(owner,suffix,left ? 1 : -1,widths,limits,COMPACT_GAP);', text)
        self.assertIn('private static const COMPACT_GAP:Number=2;', text)

    def test_extra_field_overlays_reserve_nothing_and_independent_bands_push_the_cursor(self):
        text = self.read(TABLES)
        bands = text[text.index('private function extraBands'):text.index('private function pushClear')]
        self.assertIn('if (lo>=cLo && hi<=cHi) { ++overlays; continue; }', bands)
        push = text[text.index('private function pushClear'):text.index('public function draw(')]
        self.assertIn('cursor=outward<0 ? Number(band.lo)-gap : Number(band.hi)+gap;', push)
        geometry = text[text.index('private function loadingGeometry'):text.index('private function extraBands')]
        self.assertIn('cursor=pushClear(cursor,nick,outward,bands,gap);', geometry)
        self.assertIn('exterior=left ? Math.min(exterior,Number(band.lo)) : Math.max(exterior,Number(band.hi));', geometry)

    def test_extra_field_widths_are_cached_with_the_widths_and_never_measured_per_frame(self):
        text = self.read(TABLES)
        widths = text[text.index('private function loadingWidths'):text.index('private function loadingLimits')]
        self.assertIn('fieldsAlly:fieldsAlly,fieldsEnemy:fieldsEnemy', widths)
        self.assertIn('measureRaw(field.format,fmt)', widths)
        self.assertNotIn('measureRaw', text[text.index('private function extraBands'):text.index('private function pushClear')])

    def test_header_icons_are_bound_by_confirmed_names_and_moved_from_base_positions(self):
        text = self.read(TABLES)
        self.assertIn('var icons:Array=headerIcons(owner,left,header);', text)
        self.assertIn('for each (var icon:DisplayObject in icons) state.setValue(icon,"x",state.base(icon,"x")+delta);', text)
        self.assertIn('HEADER_ICONS_ALLY:Array=["leftSquad","leftTank"]', text)
        self.assertIn('HEADER_ICONS_ENEMY:Array=["rightSquad","rightTank"]', text)
        self.assertIn('var icon:DisplayObject=parent.getChildByName(iconName);', text)
        # The beta.13 proximity heuristic is gone.
        self.assertNotIn('gapX<=48', text)

    def test_background_is_inserted_directly_above_the_native_table_background(self):
        text = self.read(TABLES)
        body = text[text.index('private function updateSubstrate'):text.index('private function substrateKey')]
        self.assertIn('var background:DisplayObject=findHeader(owner,"formBackgroundTable");', body)
        self.assertIn('var index:int=background && background.parent===host ? host.getChildIndex(background)+1', body)
        self.assertIn('host.addChildAt(shape,Math.min(index,host.numChildren));', body)

    def test_background_opacity_is_the_owner_requested_initial_value(self):
        self.assertIn('private static const BG_ALPHA:Number=0.65;', self.read(TABLES))

class LoadingLayoutModelTests(RuntimeTest):
    # Runtime-shaped inputs (values are examples, never hardcoded in the source).
    ANCHOR = 998.0
    PRESTIGE = 37.0
    CLASS = 24.0
    VEHICLE = 192.0
    NICK = 150.0

    def test_columns_are_ordered_and_do_not_overlap(self):
        g = column_geometry(self.ANCHOR, self.PRESTIGE, self.CLASS, self.VEHICLE, self.NICK)
        self.assertLessEqual(g['prestige'][1], self.ANCHOR)
        self.assertLessEqual(g['klass'][1], g['prestige'][0] - GAP + 1e-9)
        self.assertLessEqual(g['vehicle'][1], g['klass'][0] - GAP + 1e-9)
        self.assertLessEqual(g['nick'][1], g['vehicle'][0] - GAP + 1e-9)

    def test_prestige_and_class_never_collide_for_the_widest_prestige(self):
        for prestige in (10.0, 26.0, 37.0):
            g = column_geometry(self.ANCHOR, prestige, self.CLASS, self.VEHICLE, self.NICK)
            self.assertGreaterEqual(g['prestige'][0] - g['klass'][1], GAP - 1e-9)

    def test_shared_anchor_gives_identical_right_edges_for_every_row(self):
        rights = set()
        for prestige in (26.0, 30.0, 37.0):
            rights.add(column_geometry(self.ANCHOR, prestige, self.CLASS, self.VEHICLE, self.NICK)['prestige'][1])
        self.assertEqual(rights, {self.ANCHOR - GAP})

    def test_mirrored_enemy_geometry_matches_the_ally_layout(self):
        g = column_geometry(self.ANCHOR, self.PRESTIGE, self.CLASS, self.VEHICLE, self.NICK)
        centre = 1280.0
        enemy = mirror(g, centre)
        self.assertAlmostEqual(enemy['nick'][0] - enemy['vehicle'][1], GAP)
        self.assertAlmostEqual(enemy['vehicle'][0] - enemy['klass'][1], GAP)
        self.assertAlmostEqual(enemy['klass'][0] - enemy['prestige'][1], GAP)

    def test_reservation_covers_the_estimate_and_never_shrinks(self):
        width = reserve(0.0, actual=132.0, estimate=193.0)
        self.assertEqual(width, 193.0 + 6.0)
        self.assertEqual(reserve(width, actual=132.0, estimate=132.0), width)

    def test_asynchronous_arrival_does_not_change_the_reservation(self):
        before = reserve(0.0, actual=132.0, estimate=193.0)
        after = reserve(before, actual=193.0, estimate=193.0)
        self.assertEqual(before, after)

    def test_expansion_is_only_for_real_content_larger_than_the_estimate(self):
        width = reserve(0.0, actual=132.0, estimate=193.0)
        grown = reserve(width, actual=210.0, estimate=193.0)
        self.assertEqual(grown, 210.0 + 6.0)

    def test_repeated_application_has_no_cumulative_offsets(self):
        first = column_geometry(self.ANCHOR, self.PRESTIGE, self.CLASS, self.VEHICLE, self.NICK)
        for _ in range(50):
            again = column_geometry(self.ANCHOR, self.PRESTIGE, self.CLASS, self.VEHICLE, self.NICK)
        self.assertEqual(first, again)

    def test_narrow_viewport_is_reported_as_overflow(self):
        limit_left = 600.0
        g = column_geometry(self.ANCHOR, self.PRESTIGE, self.CLASS, self.VEHICLE, self.NICK)
        overflow = max(0.0, limit_left - g['nick'][0])
        self.assertGreater(overflow, 0.0)

    def test_mirrored_native_prestige_gap_equals_the_configured_gap(self):
        # Ally prestige extends towards negative x from its origin (occupied offset -width). Placed by its right edge,
        # the visible gap to the contour is exactly GAP; the beta.9 origin placement left a gap of width + GAP.
        anchor, width, rel = 998.0, 26.0, -26.0
        origin = (anchor - GAP) - rel - width
        self.assertAlmostEqual(anchor - (origin + rel + width), GAP)

    def test_disabled_class_releases_its_column(self):
        with_class = column_geometry(self.ANCHOR, self.PRESTIGE, self.CLASS, self.VEHICLE, self.NICK)
        without = column_geometry(self.ANCHOR, self.PRESTIGE, 0.0, self.VEHICLE, self.NICK)
        self.assertGreater(without['vehicle'][0], with_class['vehicle'][0])
        self.assertAlmostEqual(without['vehicle'][1], self.ANCHOR - GAP - self.PRESTIGE - GAP)

    def test_disabled_prestige_releases_its_column(self):
        with_prestige = column_geometry(self.ANCHOR, self.PRESTIGE, self.CLASS, self.VEHICLE, self.NICK)
        without = column_geometry(self.ANCHOR, 0.0, self.CLASS, self.VEHICLE, self.NICK)
        self.assertGreater(without['vehicle'][0], with_prestige['vehicle'][0])

    @staticmethod
    def outer_columns(nick_left, badge, squad):
        # Model of the ally badge and squad columns (outward = negative x), one shared column each.
        badge_anchor = nick_left - GAP
        squad_anchor = badge_anchor - (badge + GAP if badge > 0 else 0)
        outer = nick_left
        if badge > 0:
            outer = badge_anchor - badge
        if squad > 0:
            outer = squad_anchor - squad
        return badge_anchor, squad_anchor, outer

    def test_badges_and_squads_sit_one_gap_from_the_nick_column(self):
        badge_anchor, _, _ = self.outer_columns(577.0, 24.0, 18.0)
        self.assertAlmostEqual(577.0 - badge_anchor, GAP)

    def test_disabled_badges_release_their_column(self):
        _, squad_with, outer_with = self.outer_columns(577.0, 24.0, 18.0)
        _, squad_without, outer_without = self.outer_columns(577.0, 0.0, 18.0)
        self.assertGreater(outer_without, outer_with)
        # Without badges the squad column moves inward (towards the nick) by the badge width plus one gap.
        self.assertAlmostEqual(squad_without - squad_with, 24.0 + GAP)

    def test_background_covers_the_occupied_table_on_one_side_only(self):
        # Ally substrate spans from the outermost content to the contour's inner edge, never past the centre.
        anchor, contour, nick_left = 998.0, 80.0, 577.0
        _, _, outer = self.outer_columns(nick_left, 24.0, 18.0)
        x0, x1 = outer - 6.0, anchor + contour + 6.0
        self.assertLessEqual(x0, outer)
        self.assertGreaterEqual(x1, anchor + contour)
        self.assertLess(x1, 1102.0)  # the central map starts at 1102 (global) in the captured layout

    def test_background_extent_follows_the_table_not_a_fixed_width(self):
        # A nick column further outward (smaller x) moves the outer edge outward; the substrate follows it.
        narrow = self.outer_columns(700.0, 24.0, 18.0)[2]
        wide = self.outer_columns(577.0, 24.0, 18.0)[2]
        self.assertLess(wide, narrow)

    def test_extra_field_inside_the_contour_is_an_intended_overlay(self):
        # Clan icon at x=65 bound to the contour: lies fully inside the contour span, so it is not a collision.
        anchor, outer = 998.0, 527.0
        lo, hi = anchor + 65.0, anchor + 65.0 + 16.0
        self.assertFalse(lo < anchor and hi > outer)

    def test_extra_field_reaching_the_text_columns_is_reported_as_collision(self):
        # A field that reaches from the prestige band back over the table text is a collision.
        anchor, outer = 998.0, 527.0
        lo, hi = anchor - 30.0, anchor - 10.0
        self.assertTrue(lo < anchor and hi > outer)

    @staticmethod
    def push_clear(cursor, width, outward, bands, gap):
        # Model of tablerenderer.pushClear: a column is moved outward past every band it overlaps.
        guard, moved = 0, True
        while moved and guard <= len(bands):
            moved, guard = False, guard + 1
            col_lo = cursor - width if outward < 0 else cursor
            col_hi = cursor if outward < 0 else cursor + width
            for lo, hi in bands:
                if hi > col_lo and lo < col_hi:
                    cursor = lo - gap if outward < 0 else hi + gap
                    moved = True
                    break
        return cursor

    @staticmethod
    def classify(lo, hi, c_lo, c_hi):
        # Overlay when fully inside the contour span; otherwise an independent band.
        return 'overlay' if lo >= c_lo and hi <= c_hi else 'band'

    def test_independent_band_pushes_the_nick_column_past_it(self):
        self.assertAlmostEqual(self.push_clear(600.0, 150.0, -1, [(500.0, 560.0)], GAP), 500.0 - GAP)

    def test_band_outside_the_table_does_not_push(self):
        self.assertEqual(self.push_clear(600.0, 150.0, -1, [(100.0, 200.0)], GAP), 600.0)

    def test_enemy_band_pushes_outward_mirrored(self):
        self.assertAlmostEqual(self.push_clear(1400.0, 150.0, 1, [(1440.0, 1500.0)], GAP), 1500.0 + GAP)

    def test_contour_overlay_is_not_an_independent_band(self):
        anchor, contour = 998.0, 80.0
        self.assertEqual(self.classify(anchor + 65.0, anchor + 79.0, anchor, anchor + contour), 'overlay')
        self.assertEqual(self.classify(anchor - 30.0, anchor + 10.0, anchor, anchor + contour), 'band')
