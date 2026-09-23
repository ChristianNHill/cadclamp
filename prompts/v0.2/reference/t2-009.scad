// t2-009 wall-mounted tool holder
$fn = 96;
bore_diameter = 28;
collar_height = 25;
plate_width = 60;
plate_height = 90;
plate_thickness = 4;
collar_od = 44;
screw_diameter = 5;
screw_y = 35;

difference() {
    union() {
        translate([-plate_width / 2, -plate_height / 2, 0])
            cube([plate_width, plate_height, plate_thickness]);
        translate([0, 0, plate_thickness - 0.01])
            cylinder(d = collar_od, h = collar_height + 0.01);
    }
    translate([0, 0, -1]) cylinder(d = bore_diameter, h = plate_thickness + collar_height + 2);
    for (s = [-1, 1])
        translate([0, s * screw_y, -1]) cylinder(d = screw_diameter, h = plate_thickness + 2);
}
