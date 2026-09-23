// Nut-trap bracket: horizontal M5 clearance hole, hex pocket for an M5 nut
// with a drop-in slot from the top. Plain round hole (reference, no DfAM).
$fn = 96;
bolt_hole_diameter = 5.5;
nut_across_flats = 8.4;
nut_pocket_thickness = 4.4;
axis_z = 20;
difference() {
    translate([-20, -10, 0]) cube([40, 20, 30]);
    translate([0, 0, axis_z]) rotate([90, 0, 0]) cylinder(d = bolt_hole_diameter, h = 22, center = true);
    // hex pocket, flats vertical so the 8.4 mm across-flats runs along X
    translate([0, 0, axis_z]) rotate([90, 0, 0]) rotate([0, 0, 30])
        cylinder(d = nut_across_flats / cos(30), h = nut_pocket_thickness, center = true, $fn = 6);
    translate([-nut_across_flats / 2, -nut_pocket_thickness / 2, axis_z]) cube([nut_across_flats, nut_pocket_thickness, 11]);
}
