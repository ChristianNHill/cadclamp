stand_width = 90; base_depth = 70; base_thickness = 6;
lean_angle = 60; backrest_thickness = 6; backrest_top_z = 58;
lip_height = 12; lip_thickness = 6;
rise = backrest_top_z - base_thickness;
run = rise / tan(lean_angle);
shift = backrest_thickness / sin(lean_angle); // horizontal offset of the front face
// YZ profile, extruded along X: 2D x -> Y, 2D y -> Z
module yz(pts) translate([-stand_width/2, 0, 0]) rotate([90, 0, 90]) linear_extrude(stand_width) polygon(pts);
union() {
  translate([-stand_width/2, 0, 0]) cube([stand_width, base_depth, base_thickness]);
  yz([[base_depth, base_thickness - 1], [base_depth, base_thickness],
      [base_depth - run, backrest_top_z], [base_depth - run - shift, backrest_top_z],
      [base_depth - shift, base_thickness], [base_depth - shift, base_thickness - 1]]);
  translate([-stand_width/2, 0, base_thickness - 1]) cube([stand_width, lip_thickness, lip_height + 1]);
}
