// Ball joint rod end printed assembled. Ball and housing both stand on the
// bed; the ball's lower half and the housing's upper inner face are both
// within 39 degrees of vertical, so neither needs support. The housing
// opening at each face (r 6.12) is smaller than the ball (r 7.15): captive.
ball_width = 9;
bore_diameter = 6;
clearance = 0.45;
ball_d = 14.3;
eye_d = 19;
shank_w = 11;
shank_end = 30;
tap_drill = 5.0;
thread_depth = 14;
$fn = 96;

zc = ball_width/2;
ball_r = ball_d/2;
seat_r = ball_r + clearance;

module drop_x(d, len) {
    // axis along X, point towards +Z
    rotate([0, 90, 0]) linear_extrude(len)
        hull() {
            circle(d = d, $fn = 48);
            translate([-d/2*sqrt(2), 0]) square(0.01, center = true);
        }
}

// ball
difference() {
    intersection() {
        translate([0, 0, zc]) sphere(r = ball_r);
        translate([-ball_r, -ball_r, 0]) cube([ball_d, ball_d, ball_width]);
    }
    translate([0, 0, -1]) cylinder(d = bore_diameter + 0.1, h = ball_width + 2);
}

// housing
difference() {
    union() {
        cylinder(d = eye_d, h = ball_width);
        translate([0, -shank_w/2, 0]) cube([shank_end, shank_w, ball_width]);
    }
    translate([0, 0, zc]) sphere(r = seat_r);
    translate([shank_end - thread_depth, 0, zc]) drop_x(tap_drill, thread_depth + 1);
}
