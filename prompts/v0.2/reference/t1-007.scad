outer_length = 60; outer_width = 40; outer_height = 30; wall_thickness = 2.4; floor_thickness = 2.4;
difference() {
  translate([-outer_length/2, -outer_width/2, 0]) cube([outer_length, outer_width, outer_height]);
  translate([-outer_length/2 + wall_thickness, -outer_width/2 + wall_thickness, floor_thickness])
    cube([outer_length - 2*wall_thickness, outer_width - 2*wall_thickness, outer_height]);
}
