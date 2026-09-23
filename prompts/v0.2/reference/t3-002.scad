// t3-002 fluid manifold block
$fn = 96;
block_length = 60;
block_width = 40;
block_height = 30;
channel_diameter = 10;
run_z = 15;
branch_depth = 20;
mount_diameter = 5.5;
mount_x = 25;
mount_y = 15;

difference() {
    translate([-block_length / 2, -block_width / 2, 0])
        cube([block_length, block_width, block_height]);
    translate([-block_length / 2 - 1, 0, run_z]) rotate([0, 90, 0])
        cylinder(d = channel_diameter, h = block_length + 2);
    translate([0, 0, block_height - branch_depth])
        cylinder(d = channel_diameter, h = branch_depth + 1);
    for (sx = [-1, 1], sy = [-1, 1])
        translate([sx * mount_x, sy * mount_y, -1])
            cylinder(d = mount_diameter, h = block_height + 2);
}
