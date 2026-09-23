// t3-005 open-top storage box with dividers and lid lip
outer_length = 90;
outer_width = 60;
outer_height = 30;
wall_thickness = 2.4;
divider_x = 28;
lip_thickness = 1.6;
lip_height = 3;
lip_inset = (wall_thickness - lip_thickness) / 2;

module rect_ring(l, w, t, h) {
    difference() {
        translate([-l / 2, -w / 2, 0]) cube([l, w, h]);
        translate([-l / 2 + t, -w / 2 + t, -1]) cube([l - 2 * t, w - 2 * t, h + 2]);
    }
}

union() {
    difference() {
        translate([-outer_length / 2, -outer_width / 2, 0])
            cube([outer_length, outer_width, outer_height]);
        translate([-outer_length / 2 + wall_thickness, -outer_width / 2 + wall_thickness, wall_thickness])
            cube([outer_length - 2 * wall_thickness, outer_width - 2 * wall_thickness, outer_height]);
    }
    // dividers overlap walls/floor slightly for a clean union
    for (s = [-1, 1])
        translate([s * divider_x - wall_thickness / 2, -outer_width / 2 + wall_thickness - 0.01, wall_thickness - 0.01])
            cube([wall_thickness, outer_width - 2 * wall_thickness + 0.02, outer_height - wall_thickness + 0.01]);
    translate([0, 0, outer_height - 0.01])
        rect_ring(outer_length - 2 * lip_inset, outer_width - 2 * lip_inset, lip_thickness, lip_height + 0.01);
}
