// t4-006 socket half of a ball joint
ball_diameter = 20;
joint_clearance = 0.4;
mouth_diameter = 17;
plate = [44, 30, 5];
body_d = 26;
top = 33;
cz = 22;
$fn = 96;

cavity_d = ball_diameter + 2 * joint_clearance;
difference() {
    union() {
        translate([-plate.x/2, -plate.y/2, 0]) cube(plate);
        translate([0, 0, plate.z - 1]) cylinder(d = body_d, h = top - plate.z + 1);
    }
    for (x = [-17, 17]) translate([x, 0, -1]) cylinder(d = 4.5, h = plate.z + 2);
    translate([0, 0, cz]) sphere(d = cavity_d);
    translate([0, 0, cz]) cylinder(d = mouth_diameter, h = top - cz + 1);
}
