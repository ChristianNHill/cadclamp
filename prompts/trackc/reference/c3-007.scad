// Base-mount bearing housing: a base plate with a tower round the bearing.
// The bore has a teardrop crown (point up) so its top prints without support.
bearing_diameter = 22;
shaft_height = 19;
bolt_spacing = 64;
bolt_hole = 8.73;
length = 83;
depth = 16;
height = 40;
base = 8;
tower = 36;
chamfer = 5;
fit = 0.1;              // bore allowance for a light press fit
$fn = 96;

r = bearing_diameter/2 + fit;

difference() {
    rotate([90, 0, 0]) linear_extrude(depth, center = true)
        union() {
            translate([-length/2, 0]) square([length, base]);
            polygon([[-tower/2, 0], [tower/2, 0], [tower/2, height - chamfer],
                      [tower/2 - chamfer, height], [-tower/2 + chamfer, height],
                      [-tower/2, height - chamfer]]);
        }
    rotate([90, 0, 0]) linear_extrude(depth + 2, center = true)
        hull() {
            translate([0, shaft_height]) circle(r = r);
            translate([0, shaft_height + r*sqrt(2)]) square(0.01, center = true);
        }
    for (x = [-bolt_spacing/2, bolt_spacing/2])
        translate([x, 0, -1]) cylinder(d = bolt_hole, h = base + 2);
}
