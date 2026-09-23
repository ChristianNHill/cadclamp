// t3-001 mounting bracket with boss and counterbored holes
$fn = 96;
plate_length = 70;
plate_width = 40;
plate_thickness = 6;
boss_diameter = 22;
boss_height = 14;
bore_diameter = 10;
hole_x = 26;
hole_diameter = 5.5;
cbore_diameter = 10;
cbore_depth = 3.4;

difference() {
    union() {
        translate([-plate_length / 2, -plate_width / 2, 0])
            cube([plate_length, plate_width, plate_thickness]);
        translate([0, 0, plate_thickness - 0.01])
            cylinder(d = boss_diameter, h = boss_height + 0.01);
    }
    translate([0, 0, -1]) cylinder(d = bore_diameter, h = plate_thickness + boss_height + 2);
    for (s = [-1, 1]) translate([s * hole_x, 0, 0]) {
        translate([0, 0, -1]) cylinder(d = hole_diameter, h = plate_thickness + 2);
        translate([0, 0, plate_thickness - cbore_depth]) cylinder(d = cbore_diameter, h = cbore_depth + 1);
    }
}
