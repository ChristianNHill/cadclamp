// Corner bracket, printed as an L on its flat leg. The upright hole is a
// teardrop (point up) and two side gussets stiffen the bend.
leg_length = 40;
bracket_width = 23.8;
hole_diameter = 5.1;
hole_offset = 30.2;
thickness = 3;
gusset = 2;
$fn = 64;

module leg_outline() {
    // rounded-end leg in its own plane: u along the leg, v across it
    hull() {
        translate([0, -bracket_width/2]) square([1, bracket_width]);
        translate([leg_length - bracket_width/2, 0]) circle(d = bracket_width);
    }
}

module teardrop(d, h) {
    // axis along X, point towards +Z
    rotate([0, 90, 0]) rotate([0, 0, 0]) linear_extrude(h, center = true)
        hull() {
            circle(d = d);
            translate([-d/2*sqrt(2), 0]) square(0.01, center = true);
        }
}

difference() {
    union() {
        linear_extrude(thickness) leg_outline();
        // upright leg: outline in the YZ plane, extruded along +X
        rotate([0, -90, 0]) translate([0, 0, -thickness]) linear_extrude(thickness) leg_outline();
        for (y = [-bracket_width/2, bracket_width/2 - gusset])
            translate([0, y + gusset, 0]) rotate([90, 0, 0]) linear_extrude(gusset)
                polygon([[0, 0], [22, 0], [0, 22]]);
    }
    translate([hole_offset, 0, -1]) cylinder(d = hole_diameter, h = thickness + 2);
    translate([thickness/2, 0, hole_offset]) teardrop(hole_diameter, thickness + 2);
}
