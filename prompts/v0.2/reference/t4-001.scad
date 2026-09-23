// t4-001 cantilever snap-fit hook
beam_length = 30;
beam_thickness = 3;
barb_depth = 2.5;
barb_height = 8;
pad = [24, 20, 6];
beam_width = 8;

top = pad.z + beam_length;
bx = beam_thickness / 2;

translate([-pad.x/2, -pad.y/2, 0]) cube(pad);
// beam + barb as one XZ profile extruded across Y; bottom sunk 1 mm into the pad
rotate([90, 0, 0]) linear_extrude(height = beam_width, center = true)
    polygon([[-bx, pad.z - 1], [bx, pad.z - 1], [bx, top - barb_height],
             [bx + barb_depth, top - barb_height], [bx, top], [-bx, top]]);
