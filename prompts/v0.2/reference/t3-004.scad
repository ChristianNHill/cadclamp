// t3-004 stepped pulley with keyed bore
$fn = 96;
large_diameter = 60;
large_height = 18;
small_diameter = 36;
small_height = 14;
bore_diameter = 12;
keyway_width = 4;
keyway_depth_from_axis = 8;
total_height = large_height + small_height;

difference() {
    union() {
        cylinder(d = large_diameter, h = large_height);
        translate([0, 0, large_height - 0.01])
            cylinder(d = small_diameter, h = small_height + 0.01);
    }
    translate([0, 0, -1]) cylinder(d = bore_diameter, h = total_height + 2);
    translate([-keyway_width / 2, 0, -1])
        cube([keyway_width, keyway_depth_from_axis, total_height + 2]);
}
