plate_width = 40; plate_height = 70; plate_thickness = 5; hole_diameter = 5; hole_y = 25;
peg_diameter = 14; peg_length = 35; stop_diameter = 20; stop_thickness = 4;
$fn = 96;
difference() {
  union() {
    translate([-plate_width/2, -plate_height/2, 0]) cube([plate_width, plate_height, plate_thickness]);
    translate([0, 0, plate_thickness - 0.5]) cylinder(d = peg_diameter, h = peg_length + 1);
    translate([0, 0, plate_thickness + peg_length]) cylinder(d = stop_diameter, h = stop_thickness);
  }
  for (y = [-hole_y, hole_y])
    translate([0, y, -1]) cylinder(d = hole_diameter, h = plate_thickness + 2);
}
