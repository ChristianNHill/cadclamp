// t2-010 C-clamp frame
$fn = 96;
throat_depth = 45;   // jaw opening depth in X
jaw_opening = 50;    // jaw opening height in Z
body_width = 20;
frame_x = 70;
frame_z = 80;
arm_thickness = 15;
screw_x = 50;
screw_diameter = 10.5;

difference() {
    translate([0, body_width / 2, 0]) rotate([90, 0, 0])
        linear_extrude(body_width)
            difference() {
                square([frame_x, frame_z]);
                translate([frame_x - throat_depth, arm_thickness])
                    square([throat_depth + 1, jaw_opening]);
            }
    translate([screw_x, 0, arm_thickness + jaw_opening - 1])
        cylinder(d = screw_diameter, h = arm_thickness + 2);
}
