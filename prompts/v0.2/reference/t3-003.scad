// t3-003 flanged pipe section
$fn = 96;
flange_diameter = 90;
flange_thickness = 8;
pipe_od = 44;
overall_height = 50;
bore_diameter = 30;
bolt_circle_diameter = 70;
bolt_hole_diameter = 7;

difference() {
    union() {
        cylinder(d = flange_diameter, h = flange_thickness);
        translate([0, 0, flange_thickness - 0.01])
            cylinder(d = pipe_od, h = overall_height - flange_thickness + 0.01);
    }
    translate([0, 0, -1]) cylinder(d = bore_diameter, h = overall_height + 2);
    for (a = [0 : 60 : 300])
        rotate([0, 0, a]) translate([bolt_circle_diameter / 2, 0, -1])
            cylinder(d = bolt_hole_diameter, h = flange_thickness + 2);
}
