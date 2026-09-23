// t3-009 spool
$fn = 96;
flange_diameter = 64;
flange_thickness = 4;
hub_diameter = 36;
hub_length = 40;
bore_diameter = 16;
lightening_diameter = 10;
lightening_circle = 48;
total_length = hub_length + 2 * flange_thickness;

difference() {
    union() {
        cylinder(d = flange_diameter, h = flange_thickness);
        translate([0, 0, flange_thickness - 0.01]) cylinder(d = hub_diameter, h = hub_length + 0.02);
        translate([0, 0, flange_thickness + hub_length]) cylinder(d = flange_diameter, h = flange_thickness);
    }
    translate([0, 0, -1]) cylinder(d = bore_diameter, h = total_length + 2);
    for (a = [45 : 90 : 315], z0 = [0, flange_thickness + hub_length])
        rotate([0, 0, a]) translate([lightening_circle / 2, 0, z0 - 1])
            cylinder(d = lightening_diameter, h = flange_thickness + 2);
}
