cable_diameter = 6; clearance = 0.2; wall_thickness = 2;
base_length = 30; base_width = 14; base_thickness = 3;
screw_hole_diameter = 3.5; screw_hole_x = 11;
collar_axis_z = 6; gap_angle = 90;
inner_r = cable_diameter/2 + clearance; outer_r = inner_r + wall_thickness;
$fn = 96;
difference() {
  union() {
    translate([-base_length/2, -base_width/2, 0]) cube([base_length, base_width, base_thickness]);
    // collar: axis along Y at (X=0, Z=collar_axis_z), 90 deg gap centred on +Z
    translate([0, 0, collar_axis_z]) rotate([90, 0, 0]) difference() {
      cylinder(r = outer_r, h = base_width, center = true);
      cylinder(r = inner_r, h = base_width + 2, center = true);
      // gap wedge: +/-45 deg about the local +Y (= world +Z)
      linear_extrude(base_width + 2, center = true)
        polygon([[0, 0], [2*outer_r*sin(gap_angle/2), 2*outer_r*cos(gap_angle/2)],
                 [-2*outer_r*sin(gap_angle/2), 2*outer_r*cos(gap_angle/2)]]);
    }
  }
  for (x = [-screw_hole_x, screw_hole_x])
    translate([x, 0, -1]) cylinder(d = screw_hole_diameter, h = base_thickness + 2);
}
