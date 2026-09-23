// t3-008 gusseted right-angle bracket
$fn = 96;
plate_width = 60;
plate_thickness = 6;
vertical_height = 70;
horizontal_depth = 58;
gusset_thickness = 5;
gusset_y_leg = 36;
gusset_z_leg = 50;
gusset_x = 20;
hole_diameter = 6.5;
vhole_z = 60;
hhole_y = 50;

difference() {
    union() {
        translate([-plate_width / 2, 0, 0]) cube([plate_width, plate_thickness, vertical_height]);
        translate([-plate_width / 2, 0, 0]) cube([plate_width, horizontal_depth, plate_thickness]);
        for (s = [-1, 1])
            translate([s * gusset_x - gusset_thickness / 2, 0, 0])
                rotate([90, 0, 90]) linear_extrude(gusset_thickness)
                    polygon([
                        [plate_thickness, plate_thickness],
                        [plate_thickness + gusset_y_leg, plate_thickness],
                        [plate_thickness, plate_thickness + gusset_z_leg]
                    ]);
    }
    for (s = [-1, 1]) {
        translate([s * gusset_x, -1, vhole_z]) rotate([-90, 0, 0])
            cylinder(d = hole_diameter, h = plate_thickness + 2);
        translate([s * gusset_x, hhole_y, -1])
            cylinder(d = hole_diameter, h = plate_thickness + 2);
    }
}
