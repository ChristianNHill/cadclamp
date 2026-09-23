shelf_depth = 70; wall_height = 80; plate_thickness = 5; width = 40;
rib_thickness = 4; rib_leg_x = 60; rib_leg_z = 65;
hole_diameter = 5.5; hole_y = 12; wall_hole_z = 65; shelf_hole_x = 55;
$fn = 96;
t = plate_thickness;
difference() {
  union() {
    translate([0, -width/2, 0]) cube([t, width, wall_height]);
    translate([0, -width/2, 0]) cube([shelf_depth, width, t]);
    // XZ triangle, sunk 1 mm into both plates; 2D (x,y) -> (X,Z)
    rotate([90, 0, 0]) linear_extrude(rib_thickness, center = true)
      polygon([[t - 1, t - 1], [t + rib_leg_x, t - 1], [t + rib_leg_x, t], [t, t + rib_leg_z], [t - 1, t + rib_leg_z]]);
  }
  for (y = [-hole_y, hole_y]) {
    translate([-1, y, wall_hole_z]) rotate([0, 90, 0]) cylinder(d = hole_diameter, h = t + 2);
    translate([shelf_hole_x, y, -1]) cylinder(d = hole_diameter, h = t + 2);
  }
}
