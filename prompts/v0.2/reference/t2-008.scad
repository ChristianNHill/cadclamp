// t2-008 bolted hose clamp jaw half
$fn = 96;
hose_diameter = 25;
wall_thickness = 5;
jaw_width = 15;
axis_z = 8;
r_in = hose_diameter / 2;
r_out = r_in + wall_thickness;
flange_inner_x = 12.5;
flange_outer_x = 29.5;
flange_thickness = 8;
bolt_x = 23.5;
bolt_diameter = 5.5;

difference() {
    union() {
        // semicircular arch above the axis, extruded along +Y
        translate([0, 0, axis_z]) rotate([-90, 0, 0])
            linear_extrude(jaw_width)
                difference() {
                    circle(r = r_out);
                    circle(r = r_in);
                    translate([-r_out - 1, 0]) square([2 * r_out + 2, r_out + 1]); // drop lower half (sketch +Y maps to -Z)
                }
        for (s = [-1, 1])
            translate([s > 0 ? flange_inner_x : -flange_outer_x, 0, 0])
                cube([flange_outer_x - flange_inner_x, jaw_width, flange_thickness]);
    }
    for (s = [-1, 1])
        translate([s * bolt_x, jaw_width / 2, -1])
            cylinder(d = bolt_diameter, h = flange_thickness + 2);
}
