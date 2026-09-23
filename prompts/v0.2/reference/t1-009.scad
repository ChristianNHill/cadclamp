plate_diameter = 80; thickness = 6; centre_hole_diameter = 20; bolt_circle_diameter = 60; hole_diameter = 6;
$fn = 96;
difference() {
  cylinder(d = plate_diameter, h = thickness);
  translate([0, 0, -1]) cylinder(d = centre_hole_diameter, h = thickness + 2);
  for (a = [0, 90, 180, 270])
    rotate([0, 0, a]) translate([bolt_circle_diameter/2, 0, -1]) cylinder(d = hole_diameter, h = thickness + 2);
}
