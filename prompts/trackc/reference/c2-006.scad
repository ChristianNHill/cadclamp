// Pull handle printed standing on its legs. The grip's underside is a
// 45 degree V, so the span between the legs starts as a single bridged line
// instead of a flat 10 mm wide bridge.
hole_spacing = 96;
grip_height = 33;
grip_diameter = 10;     // grip section: 10 wide, V underside, chamfered top
leg_width = 12;
tap_drill = 3.3;
hole_depth = 12;
v_tip = 23;             // lowest point of the grip, clear of the 20 mm bar
knee = 10;
$fn = 48;

x_out = hole_spacing/2 + leg_width/2;
x_in = hole_spacing/2 - leg_width/2;
w = grip_diameter/2;

module grip(x0, x1) {
    translate([x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(x1 - x0)
        polygon([[0, v_tip], [w, v_tip + w], [w, grip_height - 1.5],
                 [w - 1.5, grip_height], [-w + 1.5, grip_height],
                 [-w, grip_height - 1.5], [-w, v_tip + w]]);
}

module leg(s) {
    hull() {
        translate([s > 0 ? x_in : -x_out, -w, 0]) cube([leg_width, 2*w, grip_height - 1.5]);
        if (s > 0) grip(x_in - knee, x_out); else grip(-x_out, -x_in + knee);
    }
}

difference() {
    union() {
        leg(-1);
        leg(1);
        grip(-x_in, x_in);
    }
    for (x = [-hole_spacing/2, hole_spacing/2])
        translate([x, 0, -1]) cylinder(d = tap_drill, h = hole_depth + 1);
}
