// t4-002 living hinge panel pair
panel_length = 40;
hinge_thickness = 0.6;
hinge_width = 4;
panel_width = 30;
panel_thickness = 3;
hole_d = 4.2;
$fn = 96;

g = hinge_width / 2;
L = g + panel_length;
difference() {
    rotate([90, 0, 0]) linear_extrude(height = panel_width, center = true)
        polygon([[-L, 0], [L, 0], [L, panel_thickness], [g, panel_thickness],
                 [g, hinge_thickness], [-g, hinge_thickness],
                 [-g, panel_thickness], [-L, panel_thickness]]);
    for (s = [-1, 1]) translate([s * (g + panel_length / 2), 0, -1])
        cylinder(d = hole_d, h = panel_thickness + 2);
}
