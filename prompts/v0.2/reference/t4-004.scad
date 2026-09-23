// t4-004 internal thread cap
cap_outer_diameter = 30;
thread_major_diameter = 20.4;
thread_pitch = 2.5;
thread_minor_diameter = thread_major_diameter - 2.7;  // 17.7
height = 18;
floor_t = 4;
flute_d = 4;
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
    cylinder(d = cap_outer_diameter, h = height);
    // thread cutter: crests of the cutter are the roots of the internal thread
    translate([0, 0, floor_t])
        thread(thread_major_diameter / 2, (thread_major_diameter - thread_minor_diameter) / 2,
               thread_pitch, height - floor_t + 1, thread_pitch / 8);
    for (a = [0:60:300]) rotate(a) translate([cap_outer_diameter / 2, 0, -1])
        cylinder(d = flute_d, h = height + 2);
}
