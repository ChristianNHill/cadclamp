// Print-in-place bearing: hub and ring are separate bodies, both on the bed,
// captive through a 45-degree ridge. The ring bore is the hub profile offset
// NORMAL to its faces, so the gap is `clearance` everywhere including on the
// ridge flanks; a purely radial offset would leave only clearance*cos(45)
// = 0.35 mm there, which is under the print-in-place minimum.
$fn = 96;
clearance = 0.5;
ridge_depth = 3;
bore_diameter = 6;
hub_r = 10; ring_or = 18; h = 12;

hub_profile = [[bore_diameter / 2, 0], [hub_r, 0], [hub_r, 3], [hub_r + ridge_depth, 6],
               [hub_r, 9], [hub_r, h], [bore_diameter / 2, h]];

rotate_extrude() polygon(hub_profile);
rotate_extrude() difference() {
    polygon([[hub_r, 0], [ring_or, 0], [ring_or, h], [hub_r, h]]);
    offset(r = clearance) polygon(hub_profile);
}
