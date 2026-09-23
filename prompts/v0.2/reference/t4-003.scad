// t4-003 external metric thread stud
thread_major_diameter = 20;
thread_pitch = 2.5;
thread_length = 30;
thread_depth = 1.53;   // minor = 16.93
flange_d = 36;
flange_t = 6;
bore_d = 8.4;
$fn = 96;

// Helical single-start 60 deg thread, right-hand: the polar cross-section of
// the trapezoidal axial profile, swept with twist = -360 * L / P (OpenSCAD
// positive twist is clockwise seen from +Z, so negative gives a right-hand helix).
// r_crest = crest (outer) radius, h = radial depth, crest = axial crest flat.
module thread(r_crest, h, P, L, crest) {
    a = h * tan(30);                 // axial run of each 30 deg flank
    root = P - crest - 2 * a;
    N = 180;
    function f(u) = u < crest ? r_crest
        : u < crest + a ? r_crest - h * (u - crest) / a
        : u < crest + a + root ? r_crest - h
        : r_crest - h + h * (u - crest - a - root) / a;
    pts = [for (i = [0:N-1]) let(t = 360 * i / N, r = f(P * i / N)) r * [cos(t), sin(t)]];
    linear_extrude(height = L, twist = -360 * L / P, slices = ceil(36 * L / P), convexity = 10)
        polygon(pts);
}

difference() {
    union() {
        cylinder(d = flange_d, h = flange_t);
        // thread starts 1 mm inside the flange to avoid a coplanar joint
        translate([0, 0, flange_t - 1])
            thread(thread_major_diameter / 2, thread_depth, thread_pitch, thread_length + 1, thread_pitch / 8);
    }
    translate([0, 0, -1]) cylinder(d = bore_d, h = flange_t + thread_length + 2);
    for (x = [-13, 13]) translate([x, 0, -1]) cylinder(d = 4.5, h = flange_t + 2);
}
