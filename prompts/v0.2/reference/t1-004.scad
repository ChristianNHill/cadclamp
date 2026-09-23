leg_length = 50; leg_width = 40; wall_thickness = 5; hole_diameter = 5.5; hole_offset = 30;
$fn = 96;
difference() {
  union() {
    cube([leg_length, leg_width, wall_thickness]);
    cube([wall_thickness, leg_width, leg_length]);
  }
  translate([hole_offset, leg_width/2, -1]) cylinder(d = hole_diameter, h = wall_thickness + 2);
  translate([-1, leg_width/2, hole_offset]) rotate([0, 90, 0]) cylinder(d = hole_diameter, h = wall_thickness + 2);
}
