// Snap clip laid flat: the 8 mm width is vertical, so the beam bends along
// its layers instead of across them.
$fn = 96;
beam_length = 30; beam_thickness = 2; barb_height = 2;
linear_extrude(8) difference() {
    union() {
        square([20, 10]);
        translate([20, 0]) square([beam_length, beam_thickness]);
        polygon([[20 + beam_length - 6, beam_thickness], [20 + beam_length - 6, beam_thickness + barb_height],
                 [20 + beam_length, beam_thickness]]);
    }
    translate([10, 5]) circle(d = 3.4);
}
