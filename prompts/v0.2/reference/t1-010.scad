outer_length = 100; outer_width = 70; thickness = 6; frame_width = 10;
difference() {
  translate([-outer_length/2, -outer_width/2, 0]) cube([outer_length, outer_width, thickness]);
  translate([-outer_length/2 + frame_width, -outer_width/2 + frame_width, -1])
    cube([outer_length - 2*frame_width, outer_width - 2*frame_width, thickness + 2]);
}
