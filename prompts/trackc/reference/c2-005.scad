// Loop clamp printed standing on its loop and tab. The loop has a pointed
// roof so its top prints without support; the tab lies flat on the bed.
cable_diameter = 12.7;
loop_width = 9.5;
hole_diameter = 4.4;
hole_x = 15.9;
wall = 1.6;
tab = 2.0;
$fn = 96;

zc = 7.95;
r = cable_diameter/2 + 0.2;

module drop(rr) {
    hull() {
        translate([0, zc]) circle(r = rr);
        translate([0, zc + rr*sqrt(2)]) square(0.01, center = true);
    }
}

difference() {
    rotate([90, 0, 0]) linear_extrude(loop_width, center = true)
        difference() {
            union() {
                intersection() {
                    drop(r + wall);
                    translate([-50, 0]) square([100, 50]);
                }
                hull() {
                    translate([0, 0]) square([1, tab]);
                    translate([hole_x + 4, 0]) square([0.01, tab]);
                }
                translate([-r - wall, 0]) square([r + wall, tab]);
            }
            drop(r);
        }
    translate([hole_x, 0, -1]) cylinder(d = hole_diameter, h = tab + 2);
}
