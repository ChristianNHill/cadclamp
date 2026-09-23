// t3-010 split shaft collar
$fn = 96;
body_diameter = 40;
body_height = 20;
bore_diameter = 20;
lug_x0 = 15;
lug_x1 = 29;
lug_half_y = 12;
slit_width = 3;
bolt_hole_diameter = 5.5;
bolt_x = 24;

difference() {
    union() {
        cylinder(d = body_diameter, h = body_height);
        translate([lug_x0, -lug_half_y, 0]) cube([lug_x1 - lug_x0, 2 * lug_half_y, body_height]);
    }
    translate([0, 0, -1]) cylinder(d = bore_diameter, h = body_height + 2);
    translate([0, -slit_width / 2, -1]) cube([lug_x1 + 1, slit_width, body_height + 2]);
    translate([bolt_x, lug_half_y + 1, body_height / 2]) rotate([90, 0, 0])
        cylinder(d = bolt_hole_diameter, h = 2 * lug_half_y + 2);
}
