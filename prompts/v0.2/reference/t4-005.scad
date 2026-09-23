// t4-005 involute spur gear, 24T module 2, 20 deg pressure angle
// "module" is an OpenSCAD keyword, so the prompt's module variable is gear_module
gear_module = 2;
tooth_count = 24;
face_width = 10;
pressure_angle = 20;
bore_d = 10;
$fn = 96;

rp = gear_module * tooth_count / 2;          // 24
ra = rp + gear_module;                       // 26
rf = rp - 1.25 * gear_module;                // 21.5
rb = rp * cos(pressure_angle);          // 22.55
function inv(a) = tan(a) - a * PI / 180;          // radians
function flank_ang(r) = 90 / tooth_count + inv(pressure_angle) * 180 / PI
                        - inv(acos(rb / max(r, rb))) * 180 / PI;   // degrees from tooth centreline
steps = 20;
flank = [for (i = [0:steps]) let(r = rb + (ra - rb) * i / steps) [r, flank_ang(r)]];
function pol(p) = p[0] * [cos(p[1]), sin(p[1])];
tooth = concat(
    [pol([rf - 0.5, -flank_ang(rb)])],
    [for (p = flank) pol([p[0], -p[1]])],
    [for (i = [steps:-1:0]) pol(flank[i])],
    [pol([rf - 0.5, flank_ang(rb)])]);

difference() {
    linear_extrude(height = face_width) union() {
        circle(r = rf);
        for (k = [0:tooth_count - 1]) rotate(k * 360 / tooth_count) polygon(tooth);
    }
    translate([0, 0, -1]) cylinder(d = bore_d, h = face_width + 2);
}
