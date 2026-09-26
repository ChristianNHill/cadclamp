// One-piece clamping shaft collar with an M3 clamp screw across the slit.
// The screw hole is a teardrop (point up); the far side has a nut pocket.
bore_diameter = 10;
outer_diameter = 25;
collar_width = 9;
slit = 1.0;
screw_x = 8.5;
screw_z = 4.5;
screw_clear = 3.4;
nut_af = 5.7;   // M3 nut across flats plus clearance
chamfer = 0.4;
$fn = 96;

module teardrop_y(d, len) {
    // axis along Y, point towards +Z
    rotate([90, 0, 0]) linear_extrude(len, center = true)
        hull() {
            circle(d = d);
            translate([0, d/2*sqrt(2)]) square(0.01, center = true);
        }
}

difference() {
    rotate_extrude()
        polygon([
            [bore_diameter/2 + chamfer, 0], [outer_diameter/2 - chamfer, 0],
            [outer_diameter/2, chamfer], [outer_diameter/2, collar_width],
            [bore_diameter/2, collar_width], [bore_diameter/2, chamfer]
        ]);
    translate([bore_diameter/2 - 1, -slit/2, -1]) cube([outer_diameter, slit, collar_width + 2]);
    translate([screw_x, 0, screw_z]) teardrop_y(screw_clear, outer_diameter + 2);
    // nut pocket on -Y, open to the outside, head counterbore on +Y
    translate([screw_x, -9, screw_z]) rotate([90, 0, 0])
        rotate([0, 0, 30]) cylinder(d = nut_af / cos(30), h = 10, $fn = 6);
    translate([screw_x, 9, screw_z]) teardrop_y(6.0, 8);
}
