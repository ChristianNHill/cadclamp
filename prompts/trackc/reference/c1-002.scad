// Two-hole pipe strap, printed standing on its feet. The roof over the pipe
// is pointed (45 degree flanks) so it prints without support.
pipe_diameter = 20.64;
hole_spacing = 69.85;
strap_width = 31.75;
hole_diameter = 11.1;
wall = 3;
foot = 3;
length = 108;
clear = 0.4;
$fn = 96;

r = pipe_diameter/2 + clear;
zc = pipe_diameter/2;

module saddle_profile(rr) {
    // circle below its centre, 45 degree roof above it (teardrop)
    hull() {
        translate([0, zc]) circle(r = rr);
        translate([0, zc + rr*sqrt(2)]) square(0.01, center = true);
    }
}

difference() {
    union() {
        translate([-length/2, -strap_width/2, 0]) cube([length, strap_width, foot]);
        rotate([90, 0, 0]) linear_extrude(strap_width, center = true)
            intersection() {
                saddle_profile(r + wall);
                translate([-50, 0]) square([100, 50]);
            }
    }
    rotate([90, 0, 0]) linear_extrude(strap_width + 2, center = true) {
        saddle_profile(r);
        translate([-r, -1]) square([2*r, zc + 1]);
    }
    for (x = [-hole_spacing/2, hole_spacing/2])
        translate([x, 0, -1]) cylinder(d = hole_diameter, h = foot + 2);
}
