outer_diameter = 16; bore_diameter = 6.4; length = 25;
$fn = 96;
difference() {
  cylinder(d = outer_diameter, h = length);
  translate([0, 0, -1]) cylinder(d = bore_diameter, h = length + 2);
}
