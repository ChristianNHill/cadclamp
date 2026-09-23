// t2-006 bail-style drawer handle
$fn = 96;
centre_distance = 96;
foot_size = 18;
grip_height = 22;      // foot height = underside of grip bar
bar_thickness = 12;
bar_length = 114;
hole_diameter = 4.5;

difference() {
    union() {
        for (s = [-1, 1])
            translate([s * centre_distance / 2 - foot_size / 2, -foot_size / 2, 0])
                cube([foot_size, foot_size, grip_height]);
        translate([-bar_length / 2, -foot_size / 2, grip_height])
            cube([bar_length, foot_size, bar_thickness]);
    }
    for (s = [-1, 1])
        translate([s * centre_distance / 2, 0, -1])
            cylinder(d = hole_diameter, h = grip_height + bar_thickness + 2);
}
