// t4-007 threaded neck adapter
socket_thread_diameter = 28;   // female major (roots)
spigot_thread_diameter = 24;   // male major (crests)
through_bore_diameter = 18;
socket_pitch = 4;
spigot_pitch = 3;
socket_depth_r = 1.5;          // 28 -> 25
spigot_depth_r = 1.5;          // 24 -> 21
body_d = 34;
body_h = 20;
socket_len = 14;
spigot_len = 20;
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
        cylinder(d = body_d, h = body_h);
        translate([0, 0, body_h - 1])
            thread(spigot_thread_diameter / 2, spigot_depth_r, spigot_pitch, spigot_len + 1, spigot_pitch / 8);
    }
    // female thread cutter, open at Z = 0
    translate([0, 0, -1])
        thread(socket_thread_diameter / 2, socket_depth_r, socket_pitch, socket_len + 1, socket_pitch / 8);
    translate([0, 0, socket_len - 1]) cylinder(d = through_bore_diameter, h = body_h + spigot_len);
}
