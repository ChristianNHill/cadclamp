// t4-008 hinge leaf with pin bore
pin_diameter = 5;
pin_clearance = 0.4;
knuckle_diameter = 10;
leaf = [46, 50, 4];
fix_d = 5;
$fn = 96;

kr = knuckle_diameter / 2;
bore = pin_diameter + pin_clearance;
difference() {
    union() {
        translate([0, -leaf.y/2, 0]) cube(leaf);
        for (y0 = [-25, 10]) translate([0, y0, kr]) rotate([-90, 0, 0])
            cylinder(r = kr, h = 15);
    }
    translate([0, -leaf.y/2 - 1, kr]) rotate([-90, 0, 0]) cylinder(d = bore, h = leaf.y + 2);
    for (y = [-16, 16]) translate([32, y, -1]) cylinder(d = fix_d, h = leaf.z + 2);
}
