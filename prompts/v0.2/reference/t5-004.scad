// Tunnel block: the 30 x 10 mm clearance envelope with a 45-degree pointed
// roof above it instead of a flat 30 mm bridge.
$fn = 96;
tunnel_width = 30; tunnel_height = 10; floor_thickness = 4;
difference() {
    translate([-25, -10, 0]) cube([50, 20, 34]);
    translate([-tunnel_width / 2, -11, floor_thickness]) cube([tunnel_width, 22, tunnel_height]);
    // roof prism in XZ, extruded along Y
    translate([0, 11, 0]) rotate([90, 0, 0]) linear_extrude(22)
        polygon([[-tunnel_width / 2, floor_thickness + tunnel_height - 0.01],
                 [tunnel_width / 2, floor_thickness + tunnel_height - 0.01],
                 [0, floor_thickness + tunnel_height + tunnel_width / 2]]);
}
