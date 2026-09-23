across_flats = 10; length = 30; bore_diameter = 4.2;
difference() {
  // $fn=6 puts a vertex on +X, so the flats are perpendicular to Y
  cylinder(r = across_flats / 2 / cos(30), h = length, $fn = 6);
  translate([0, 0, -1]) cylinder(d = bore_diameter, h = length + 2, $fn = 96);
}
