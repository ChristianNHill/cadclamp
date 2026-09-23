plate_size = 50; plate_thickness = 12; bore_diameter = 5.5; counterbore_diameter = 10; counterbore_depth = 6;
$fn = 96;
difference() {
  translate([-plate_size/2, -plate_size/2, 0]) cube([plate_size, plate_size, plate_thickness]);
  translate([0, 0, -1]) cylinder(d = bore_diameter, h = plate_thickness + 2);
  translate([0, 0, plate_thickness - counterbore_depth]) cylinder(d = counterbore_diameter, h = counterbore_depth + 1);
}
