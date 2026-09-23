// t4-009 stacking dovetail block
dovetail_width = 16;   // rail top width
dovetail_height = 8;
slide_clearance = 0.3;
block = [60, 40, 20];
rail_base = dovetail_width - 2 * dovetail_height * tan(14);  // 12 mm
$fn = 96;

c = slide_clearance;
H = block.z;
W = block.y / 2;
sb = rail_base / 2 + c;        // socket half-width at opening (6.3)
st = dovetail_width / 2 + c;   // socket half-width at deepest (8.3)
sd = dovetail_height + c;
rb = rail_base / 2;
rt = dovetail_width / 2;
difference() {
    // YZ profile (block - socket + rail) extruded along X
    rotate([90, 0, 90]) linear_extrude(height = block.x, center = true)
        polygon([[-W, 0], [-sb, 0], [-st, sd], [st, sd], [sb, 0], [W, 0],
                 [W, H], [rb, H], [rt, H + dovetail_height],
                 [-rt, H + dovetail_height], [-rb, H], [-W, H]]);
    for (x = [-22, 22], y = [-14, 14]) translate([x, y, -1]) cylinder(d = 5, h = H + 2);
}
