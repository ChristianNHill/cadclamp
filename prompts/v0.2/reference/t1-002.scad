outer_diameter = 24; inner_diameter = 10; thickness = 3;
$fn = 96;
difference() {
  cylinder(d = outer_diameter, h = thickness);
  translate([0, 0, -1]) cylinder(d = inner_diameter, h = thickness + 2);
}
