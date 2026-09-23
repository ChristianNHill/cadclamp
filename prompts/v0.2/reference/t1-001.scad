plate_length = 60; plate_width = 40; plate_thickness = 5; hole_diameter = 10;
$fn = 96;
difference() {
  translate([-plate_length/2, -plate_width/2, 0]) cube([plate_length, plate_width, plate_thickness]);
  translate([0, 0, -1]) cylinder(d = hole_diameter, h = plate_thickness + 2);
}
