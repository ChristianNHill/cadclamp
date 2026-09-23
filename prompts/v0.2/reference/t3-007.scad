// t3-007 T-slot rail
$fn = 96;
rail_length = 100;
rail_width = 40;
rail_height = 25;
neck_width = 10;
slot_width = 18;     // chamber width
chamber_bottom = 7;
chamber_top = 15;
hole_diameter = 5.5;
hole_y = 35;

difference() {
    translate([0, rail_length / 2, 0]) rotate([90, 0, 0])
        linear_extrude(rail_length)
            difference() {
                translate([-rail_width / 2, 0]) square([rail_width, rail_height]);
                translate([-neck_width / 2, chamber_top - 0.01]) square([neck_width, rail_height - chamber_top + 1]);
                translate([-slot_width / 2, chamber_bottom]) square([slot_width, chamber_top - chamber_bottom]);
            }
    for (s = [-1, 1])
        translate([0, s * hole_y, -1]) cylinder(d = hole_diameter, h = chamber_bottom + 2);
}
