ramp_length = 80; width = 40; min_height = 2; max_height = 20;
// XZ profile extruded along +Y
rotate([90, 0, 0]) translate([0, 0, -width])
  linear_extrude(width) polygon([[0, 0], [ramp_length, 0], [ramp_length, max_height], [0, min_height]]);
