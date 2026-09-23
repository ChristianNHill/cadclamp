// t4-010 hinged tube clamp
tube_diameter = 28;
wall_thickness = 4;
bolt_hole_diameter = 4.5;
height = 14;
gap = 2;
flexure_r = 16.4;
$fn = 96;

ri = tube_diameter / 2;
ro = ri + wall_thickness;
difference() {
    union() {
        cylinder(r = ro, h = height);
        translate([14, -10, 0]) cube([20, 20, height]);
    }
    translate([0, 0, -1]) cylinder(r = ri, h = height + 2);
    translate([0, -gap/2, -1]) cube([35, gap, height + 2]);
    // flexure groove: 30 deg annular sector centred on -X
    translate([0, 0, -1]) linear_extrude(height = height + 2)
        polygon(concat([for (a = [165:1:195]) flexure_r * [cos(a), sin(a)]],
                       [for (a = [195:-1:165]) (ro + 1) * [cos(a), sin(a)]]));
    translate([26, -11, 7]) rotate([-90, 0, 0]) cylinder(d = bolt_hole_diameter, h = 22);
}
