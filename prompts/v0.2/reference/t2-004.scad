body_size = 30; height = 20; bore_diameter = 12; chamfer = 1.5;
difference() {
  hull() {
    translate([-body_size/2 + chamfer, -body_size/2 + chamfer, 0]) cube([body_size - 2*chamfer, body_size - 2*chamfer, height]);
    translate([-body_size/2, -body_size/2 + chamfer, chamfer]) cube([body_size, body_size - 2*chamfer, height - 2*chamfer]);
    translate([-body_size/2 + chamfer, -body_size/2, chamfer]) cube([body_size - 2*chamfer, body_size, height - 2*chamfer]);
  }
  translate([0, 0, -1]) cylinder(d = bore_diameter, h = height + 2, $fn = 96);
}
