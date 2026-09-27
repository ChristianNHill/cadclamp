// Open-top enclosure with a PCB ledge whose underside is a 45-degree chamfer
// (the support-free answer; a flat slab ledge would be a horizontal overhang).
$fn = 96;
wall = 2; ledge_top = 25; ledge_depth = 5;
outer = [60, 40, 40];
inner = [outer[0] - 2 * wall, outer[1] - 2 * wall];
difference() {
    translate([-outer[0] / 2, -outer[1] / 2, 0]) cube(outer);
    union() {
        translate([-inner[0] / 2, -inner[1] / 2, wall]) cube([inner[0], inner[1], ledge_top - ledge_depth - wall + 0.01]);
        hull() {
            translate([-inner[0] / 2, -inner[1] / 2, ledge_top - ledge_depth]) cube([inner[0], inner[1], 0.01]);
            translate([-inner[0] / 2 + ledge_depth, -inner[1] / 2 + ledge_depth, ledge_top - 0.01])
                cube([inner[0] - 2 * ledge_depth, inner[1] - 2 * ledge_depth, 0.01]);
        }
        translate([-inner[0] / 2 + ledge_depth, -inner[1] / 2 + ledge_depth, ledge_top - 0.02])
            cube([inner[0] - 2 * ledge_depth, inner[1] - 2 * ledge_depth, 1]);
        // above the ledge: full 56 x 36 cavity, so the board rests on the ledge top
        translate([-inner[0] / 2, -inner[1] / 2, ledge_top]) cube([inner[0], inner[1], outer[2]]);
    }
}
